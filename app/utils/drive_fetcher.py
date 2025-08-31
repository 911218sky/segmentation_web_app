# GCP Console → IAM & Admin → Service Accounts → Create Service Account
# 獲取 OAuth 2.0 憑證
import io
import re
import mimetypes
import json
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import concurrent.futures

FILE_ID_RE = re.compile(r'[-\w]{25,}')

@dataclass
class DriveFetchResult:
    id: str
    name: Optional[str]
    mime_type: Optional[str]
    path: Optional[Path] = None
    size: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self):
        d = asdict(self)
        if isinstance(self.path, Path):
            d['path'] = str(self.path)
        return d

class DriveFetcher:
    # 定義 Google 原生檔案的匯出對應格式
    EXPORT_MAP = {
        'application/vnd.google-apps.document': 'application/pdf',
        'application/vnd.google-apps.spreadsheet': (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        'application/vnd.google-apps.presentation': 'application/pdf',
        'application/vnd.google-apps.drawing': 'image/png',
    }

    def __init__(
        self,
        service_account_file: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        allowed_extensions: Optional[List[str]] = None,
        max_workers: int = 1,
    ):
        # 設定允許的副檔名（小寫）
        self.allowed_exts = [e.lower() for e in (allowed_extensions or [])]
        
        # 是否保留原始資料夾結構
        self._preserve_structure = True

        # 初始化下載路徑
        self._download_dir = Path('downloads')
        
        # 初始化是否僅列出
        self._only_list = False

        # 下載佇列（儲存要並行下載的任務）
        self._download_queue: List[Dict[str, Any]] = []

        # 最大並行數
        self._max_workers = max_workers

        # 初始化 Google Drive 服務
        # _service 仍保留給主執行緒做 metadata/list（單執行緒使用）
        self._service = None
        self._creds = credentials
        self._sa_file = service_account_file
        self._init_service()

        # thread-local 快取每執行緒的 service
        self._thread_local = threading.local()

    def _init_service(self) -> None:
        # 如果已經建立過主線程 service 就直接返回
        if self._service:
            return
        # 優先使用傳入的 credentials
        if self._creds:
            creds = self._creds
        # 否則嘗試讀取 service account json
        elif self._sa_file and Path(self._sa_file).exists():
            creds = service_account.Credentials.from_service_account_file(
                self._sa_file,
                scopes=['https://www.googleapis.com/auth/drive.readonly'],
            )
        else:
            raise ValueError("請提供有效的 service_account_file 或 credentials。")
        # 建立 Drive API 客戶端（僅作 metadata/list 用）
        self._service = build('drive', 'v3', credentials=creds, cache_discovery=False)

    def _get_thread_service(self):
        """
        取得或建立目前執行緒專用的 drive service。
        這可避免跨執行緒共用 self._service，進而降低底層 C-library 的競態與崩潰風險。
        """
        if getattr(self._thread_local, 'service', None):
            return self._thread_local.service

        # 建立 thread-local 的 credentials / service
        if self._creds:
            creds = self._creds
        elif self._sa_file and Path(self._sa_file).exists():
            # 從檔案建立新的 Credentials（小量成本），更安全
            creds = service_account.Credentials.from_service_account_file(
                self._sa_file,
                scopes=['https://www.googleapis.com/auth/drive.readonly'],
            )
        else:
            raise ValueError("無可用的 credentials 或 service_account_file。")
        # 在執行緒中建立自己的 service
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
        self._thread_local.service = service
        return service

    @staticmethod
    def _safe_filename(name: str) -> str:
        # 移除檔名中非法的字元
        return re.sub(r'[\\/\?%\*:|"<>]', '', name).strip()

    @staticmethod
    def _extract_id(link: str) -> Optional[str]:
        # 從分享連結中擷取 fileId 或 folderId
        patterns = [
            r'/folders/([\w-]{25,})',
            r'/file/d/([\w-]{25,})',
            r'[?&]id=([\w-]{25,})',
            r'/d/([\w-]{25,})',
        ]
        for pat in patterns:
            m = re.search(pat, link)
            if m:
                return m.group(1)
        return None

    def _get_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        # 取得檔案或資料夾的 metadata
        try:
            return self._service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size",
                supportsAllDrives=True
            ).execute()
        except HttpError:
            return None

    def _list_folder(self, folder_id: str) -> List[Dict[str, Any]]:
        # 列出資料夾內所有檔案
        files = []
        token = None
        query = f"'{folder_id}' in parents and trashed = false"

        while True:
            resp = self._service.files().list(
                q=query,
                pageSize=200,
                fields="nextPageToken, files(id,name,mimeType,size)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                pageToken=token
            ).execute()
            files.extend(resp.get('files', []))
            token = resp.get('nextPageToken')
            if not token:
                break
        return files

    def _guess_extension(self, mime: str) -> Optional[str]:
        # 根據 MIME type 推測副檔名
        base = mime.split(';')[0].lower()
        ext = mimetypes.guess_extension(base)
        if ext:
            return ext
        # 補充常見格式
        return {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'video/mp4': '.mp4',
        }.get(base)

    def _filter_by_extension(
        self,
        filename: str,
        mime: Optional[str],
        export_mime: Optional[str]
    ) -> bool:
        # 判斷檔案是否符合允許格式
        if not self.allowed_exts:
            return True
        suffix = Path(filename).suffix.lower()
        if suffix in self.allowed_exts:
            return True
        # 嘗試用 MIME 推斷
        for candidate in filter(None, [mime, export_mime]):
            guessed = self._guess_extension(candidate)
            if guessed and guessed in self.allowed_exts:
                return True
        return False

    def _make_output_path(
        self, name: str, subdir: str, ext: str = '', create_dir: bool = True
    ) -> Path:
        safe_name = self._safe_filename(name)
        base = self._download_dir / (subdir if self._preserve_structure else '')
        out = base / f"{safe_name}{ext}"
        if create_dir:
            out.parent.mkdir(parents=True, exist_ok=True)
        return out


    def _download(self, file_id: str, dest: Path, export_mime: Optional[str] = None) -> Optional[str]:
        """
        這個方法會在各執行緒中被呼叫。
        每個執行緒會用自己的 service（透過 _get_thread_service）來取得 request，
        避免跨執行緒共用底層連線物件導致崩潰。
        """
        try:
            service = self._get_thread_service()
            if export_mime:
                request = service.files().export_media(
                    fileId=file_id,
                    mimeType=export_mime
                )
            else:
                request = service.files().get_media(
                    fileId=file_id, supportsAllDrives=True
                )
            # 以二進位寫入檔案
            with io.FileIO(dest, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            return None
        except HttpError as err:
            return str(err)
        except Exception as e:
            return str(e)

    def _process_item(
        self,
        item: Dict[str, Any],
        prefix: str,
        results: List[DriveFetchResult],
        recurse: bool
    ) -> None:
        # 處理單一項目：若為資料夾則遞迴，否則建立結果物件並把下載任務加入佇列 (不立即下載)
        fid = item['id']
        name = item.get('name', '')
        mime = item.get('mimeType', '')
        size = item.get('size')
        has_ext = Path(name).suffix.lower()

        # 資料夾處理
        if mime == 'application/vnd.google-apps.folder':
            if not recurse:
                return
            children = self._list_folder(fid)
            # 判別是否保留原本雲端資料夾結構
            new_prefix = (
                f"{prefix}{self._safe_filename(name)}/" if self._preserve_structure else ''
            )
            for child in children:
                self._process_item(child, new_prefix, results, recurse)
            return

        # 檔案處理 如果是 Google 原生檔案，則有匯出對應格式
        is_native = mime.startswith('application/vnd.google-apps')
        export_mime = self.EXPORT_MAP.get(mime) if is_native else None

        # 過濾副檔名
        if not self._filter_by_extension(name, mime, export_mime):
            return

        # 決定副檔名並生成路徑
        # 若檔名已有副檔名則使用原本副檔名，否則嘗試從 mime 推斷
        ext = '' if has_ext else (self._guess_extension(export_mime or mime) or '')
        out_path = self._make_output_path(name, prefix, ext, create_dir=not self._only_list)

        # 預先建立結果物件（先把 path / metadata 設定好）
        res = DriveFetchResult(
            id=fid,
            name=name,
            mime_type=mime,
            path=out_path,
            size=size,
            error=None,
        )
        results.append(res)
        res_index = len(results) - 1

        # 如果僅列出，則不進行下載；若檔案已存在也不進行下載
        if self._only_list:
            return

        if out_path.exists() and out_path.stat().st_size > 0:
            # 已存在，視為成功
            return

        # 否則把任務加入下載佇列，由 fetch() 最後統一並行下載
        self._download_queue.append({
            'index': res_index,
            'file_id': fid,
            'dest': out_path,
            'export_mime': export_mime if is_native else None
        })

    def fetch(
        self,
        link: str,
        download_dir: Optional[Path] = None,
        only_list: Optional[bool] = False,
        preserve_structure: Optional[bool] = True,
        allowed_extensions: Optional[List[str]] = None,
        recurse: bool = True
    ) -> List[DriveFetchResult]:
        # 設定屬性
        if download_dir:
            self._download_dir = download_dir
        self._only_list = only_list
        self._preserve_structure = preserve_structure
        
        if allowed_extensions is not None:
            self.allowed_exts = [e.lower() for e in allowed_extensions]

        # 重新初始化下載佇列與結果
        self._download_queue = []
        results: List[DriveFetchResult] = []

        # 主要接口：給定分享連結，列出或下載符合條件的所有檔案
        file_id = self._extract_id(link)
        if not file_id:
            raise ValueError("無法解析 Drive 連結的 ID。")

        metadata = self._get_metadata(file_id)
        if not metadata:
            raise RuntimeError("取得檔案 metadata 失敗。可能是權限或 ID 錯誤。")

        # 如果是資料夾，遍歷子項（但此時不立即下載）
        if metadata['mimeType'] == 'application/vnd.google-apps.folder':
            top_name = metadata.get('name', file_id)
            start_prefix = f"{self._safe_filename(top_name)}/"
            for item in self._list_folder(file_id):
                self._process_item(item, start_prefix, results, recurse)
        else:
            # 單一檔案處理
            self._process_item(metadata, '', results, recurse)

        # 若不是僅列出，並且有需要下載的任務，執行並行下載
        if not self._only_list and self._download_queue:
            # 使用 ThreadPoolExecutor 進行並行下載
            def _task_download(task):
                idx = task['index']
                fid = task['file_id']
                dest = task['dest']
                export_mime = task['export_mime']
                err = None
                try:
                    err = self._download(fid, dest, export_mime)
                except Exception as e:
                    err = str(e)
                return idx, err

            # 可以根據實際情況調整 max_workers
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as ex:
                future_to_task = {ex.submit(_task_download, t): t for t in self._download_queue}
                for fut in concurrent.futures.as_completed(future_to_task):
                    idx, err = fut.result()
                    results[idx].error = err

        return results

if __name__ == '__main__':
    SA_FILE = 'secrets/service-account.json'
    LINK = 'https://drive.google.com/file/d/1jmK_i5AvezX6fCAZLhTrxm0dUnI3KLQT/view?usp=drive_link'
    LINK = 'https://drive.google.com/drive/folders/1ngkRmMW7Aa16-yVVkHqP-C0tdllFkVCF?usp=drive_link'

    fetcher = DriveFetcher(
        service_account_file=SA_FILE,
        allowed_extensions=['.mp4', '.png', '.jpg'],
        max_workers=8,  # 並行 8 個下載工作，依網路/API 限制調整
    )
    results = fetcher.fetch(LINK, Path('downloads_simple'), only_list=False)
    print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
    print(f"總檔案數: {len(results)}")