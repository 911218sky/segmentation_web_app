import streamlit as st
from typing import Dict
from .translations import (
    TRANSLATIONS, 
    LanguageCode, 
    TranslationStrings, 
)

class LanguageManager:
    def __init__(self, default_language: LanguageCode = "zh_TW"):
        self.default_language = default_language
        self.languages: Dict[LanguageCode, str] = {
            "en": "English",
            "zh_TW": "繁體中文 (Traditional Chinese)",
            "ja": "日本語 (Japanese)",
            "ko": "한국어 (Korean)",
            "ru": "Русский (Russian)",
            "fr": "Français (French)",
            "es": "Español (Spanish)",
            "de": "Deutsch (German)",
            "ar": "العربية (Arabic)",
        }
        st.session_state.language = self.default_language

    def get_text(self, key: str) -> str:
        """獲取當前語言的翻譯文本"""
        current_lang = self.get_current_language()
        translations: TranslationStrings = TRANSLATIONS[current_lang]
        return translations[key]

    def get_current_language(self) -> LanguageCode:
        """獲取當前語言代碼"""
        if "language" not in st.session_state:
            st.session_state.language = self.default_language
        return st.session_state.language  # type: ignore

    def set_language(self, lang: LanguageCode) -> None:
        """設置當前語言"""
        if lang in self.languages:
            st.session_state.language = lang

    def get_language_selector(self) -> None:
        """創建語言選擇器"""
        current_lang = self.get_current_language()
        selected_lang = st.selectbox(
            "🌐 Language",
            options=list(self.languages.keys()),
            format_func=lambda x: self.languages[x],
            index=list(self.languages.keys()).index(current_lang),
            key="language_selector"
        )
        if selected_lang != current_lang:
            self.set_language(selected_lang)
            st.rerun()

lang_manager = LanguageManager()