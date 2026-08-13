"""Tests for iTOL API dynamic error translation."""

from pyitol.utils.reporter import ITOL_API_ERROR_TRANSLATIONS, translate_itol_api_error


class TestTranslateItolApiError:
    def test_invalid_api_key(self):
        msg = translate_itol_api_error("invalid api key")
        assert "API Key 无效" in msg
        assert "原始信息" in msg

    def test_tree_file_too_large(self):
        msg = translate_itol_api_error("Tree file too large")
        assert "树文件过大" in msg

    def test_unauthorized(self):
        msg = translate_itol_api_error("Unauthorized access")
        assert "未授权" in msg

    def test_unknown_error(self):
        msg = translate_itol_api_error("Some random error xyz")
        assert "操作失败" in msg
        assert "Some random error xyz" in msg

    def test_all_keywords_have_translation(self):
        for keyword in ITOL_API_ERROR_TRANSLATIONS:
            assert len(keyword) > 0
            assert isinstance(ITOL_API_ERROR_TRANSLATIONS[keyword], str)
