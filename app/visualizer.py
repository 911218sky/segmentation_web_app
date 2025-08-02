from typing import List, Tuple
import numpy as np
import cv2


class Visualizer:
    @staticmethod
    def visualize_vertical_lines_transparent(
        image: np.ndarray,
        lines: List[Tuple[int, int, int]],
        line_color: Tuple[int, int, int] = (255, 255, 255),
        line_thickness: int = 2,
        line_alpha: float = 0.6,
        show_points: bool = False,
        point_radius: int = 3,
        min_point_color: Tuple[int, int, int] = (255, 0, 0),
        max_point_color: Tuple[int, int, int] = (0, 0, 255)
    ) -> np.ndarray:
        """
        在圖片上繪製半透明垂直線
        
        Args:
            image: 原始圖片
            lines: 垂直線列表 [(x, min_y, max_y), ...]
            line_color: 線條顏色 (B, G, R)
            line_thickness: 線條粗細
            line_alpha: 透明度 (0-1, 0為完全透明，1為完全不透明)
            show_points: 是否顯示端點
            point_radius: 端點半徑
            min_point_color: 最小y點顏色
            max_point_color: 最大y點顏色
        
        Returns:
            繪製後的圖片
        """
        # 創建一個透明層來繪製線條
        overlay = image.copy()
        
        for x, min_y, max_y in lines:
            # 在透明層上繪製垂直線
            cv2.line(overlay, (x, min_y), (x, max_y), line_color, line_thickness)
            
            if show_points:
                # 在端點畫小圓點
                cv2.circle(overlay, (x, min_y), point_radius, min_point_color, -1)
                cv2.circle(overlay, (x, max_y), point_radius, max_point_color, -1)
        
        # 將透明層與原圖混合
        result_image = cv2.addWeighted(image, 1-line_alpha, overlay, line_alpha, 0)
        
        return result_image
   
    @staticmethod
    def visualize_vertical_lines_with_mm(
        image: np.ndarray,
        lines: List[Tuple[int, int, int]],
        pixel_size_mm: float,
        font=cv2.FONT_HERSHEY_SIMPLEX,
        font_thickness: int = 1,
        display_labels: bool = True,
        **line_kwargs
    ) -> np.ndarray:
        """
        在垂直線旁標出長度 (mm)，並在影像底部顯示平均長度。
        """
        # 先畫半透明垂直線
        vis = Visualizer.visualize_vertical_lines_transparent(
            image=image,
            lines=lines,
            **line_kwargs
        )

        # 計算每條線的長度 (mm)
        h, w = vis.shape[:2]
        lengths_mm = []
        box_pad = 2

        for x, y1, y2 in lines:
            pixel_len = abs(y2 - y1)
            mm = pixel_len * pixel_size_mm
            lengths_mm.append(mm)

            if display_labels:
                # 標出長度
                text = f"{mm:.1f} mm"
                (tw, th), _ = cv2.getTextSize(text, font, 0.2, font_thickness)

                # center label horizontally on the line, place above y1
                text_x = x - tw // 2
                text_y = max(y1 - 4, th + box_pad)          # avoid going above image

                # background rectangle coords
                top_left  = (text_x - box_pad, text_y - th - box_pad)
                bot_right = (text_x + tw + box_pad, text_y + box_pad)

                cv2.rectangle(vis, top_left, bot_right, (0, 0, 0), -1) 
                cv2.putText(vis, text, (text_x, text_y), font, 0.2,
                            (255, 255, 255), font_thickness, cv2.LINE_AA)

        # 標出平均長度
        if lengths_mm:
            avg = float(np.mean(lengths_mm))
            bottom_text = f"Mean length: {avg:.1f} mm"
            (tw, th), _ = cv2.getTextSize(bottom_text, font, 0.2, font_thickness)

            # 水平置中
            text_x = (w - tw) // 2
            text_y = h - 6 

            top_left  = (text_x - box_pad, text_y - th - box_pad)
            bot_right = (text_x + tw + box_pad, text_y + box_pad)

            cv2.rectangle(vis, top_left, bot_right, (0, 0, 0), -1)
            cv2.putText(vis, bottom_text, (text_x, text_y), font, 1,
                        (255, 255, 255), font_thickness, cv2.LINE_AA)

        return vis