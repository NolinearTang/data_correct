import re
import unicodedata

class TextProcessor:
    @staticmethod
    def fullwidth_to_halfwidth(text: str) -> str:
        # 全角转半角
        return unicodedata.normalize('NFKC', text)

    @staticmethod
    def remove_non_breaking_spaces(text: str) -> str:
        # 去除收费空格（常见为\u00A0等）
        return text.replace('\u00A0', '').replace('\u2007', '').replace('\u202F', '')

    @staticmethod
    def to_lower(text: str) -> str:
        # 大写转小写
        return text.lower()

    @staticmethod
    def remove_invisible_chars(text: str) -> str:
        # 去除各种不可见字符（如零宽空格、控制字符等）
        invisible_chars = [
            '\u200b',  # 零宽空格
            '\u200c',  # 零宽非连接符
            '\u200d',  # 零宽连接符
            '\ufeff',  # BOM
            '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',  # 方向控制符
        ]
        for ch in invisible_chars:
            text = text.replace(ch, '')
        # 去除ASCII控制字符
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)
        return text

    @staticmethod
    def normalize_spaces(text: str) -> str:
        # 不同格式的空格转为普通空格
        # 包括全角空格、各种unicode空格
        space_chars = [
            '\u3000',  # 全角空格
            '\u00A0',  # 不间断空格
            '\u2000', '\u2001', '\u2002', '\u2003', '\u2004', '\u2005',
            '\u2006', '\u2007', '\u2008', '\u2009', '\u200A', '\u202F', '\u205F', '\u2060',
        ]
        for ch in space_chars:
            text = text.replace(ch, ' ')
        return text

    @staticmethod
    def collapse_spaces(text: str) -> str:
        # 多个空格合并为一个空格
        return re.sub(r' +', ' ', text)

    @staticmethod
    def detect_continuous_english(text: str) -> list:
        """
        检测一个字符串中连续的英文
        返回所有连续英文片段的列表
        """
        pattern = r'[a-zA-Z]+'
        return re.findall(pattern, text)

    @staticmethod
    def detect_continuous_alphanumeric(text: str) -> list:
        """
        检测一个字符串中连续的英文或数字
        返回所有连续英文或数字片段的列表
        """
        pattern = r'[a-zA-Z0-9]+'
        return re.findall(pattern, text)

    @staticmethod
    def detect_continuous_custom_chars(text: str, custom_chars: str = '',
                                     start_constraint: bool = False, 
                                     end_constraint: bool = False) -> list:
        """
        检测一个字符串中连续的英文、数字以及自定义的字符列表
        
        Args:
            text: 要检测的字符串
            custom_chars: 自定义字符列表，如 '-_' 表示允许连字符和下划线
            start_constraint: 开关1，只有英文、数字以及给定的字符可以出现在首
            end_constraint: 开关2，只有英文、数字以及给定的字符可以出现在尾
        
        Returns:
            符合条件的连续字符片段列表
        """
        # 构建基础字符集：英文、数字 + 自定义字符
        base_chars = r'[a-zA-Z0-9' + re.escape(custom_chars) + r']'
        
        if start_constraint and end_constraint:
            # 首尾都有约束
            pattern = f'^{base_chars}+$'
        elif start_constraint:
            # 只有首部约束
            pattern = f'^{base_chars}+'
        elif end_constraint:
            # 只有尾部约束
            pattern = f'{base_chars}+$'
        else:
            # 无约束
            pattern = f'{base_chars}+'
        
        return re.findall(pattern, text)

    @staticmethod
    def expand_substring(text: str, substring: str, custom_chars: str = '',
                        forbidden_start_chars: str = '', forbidden_end_chars: str = '') -> str:
        """
        对子串前后进行扩展，如果前后是字母、数字以及用户给定的字符
        
        Args:
            text: 原始字符串
            substring: 要扩展的子串
            custom_chars: 用户给定的额外允许字符
            forbidden_start_chars: 开关1，不能出现在首位的字符
            forbidden_end_chars: 开关2，不能出现在末位的字符
        
        Returns:
            扩展后的完整字符串
        """
        if substring not in text:
            return substring
        
        # 构建允许扩展的字符集
        allowed_chars = r'[a-zA-Z0-9' + re.escape(custom_chars) + r']'
        
        # 构建不允许出现在首位的字符集
        forbidden_start_pattern = r'[' + re.escape(forbidden_start_chars) + r']' if forbidden_start_chars else None
        
        # 构建不允许出现在末位的字符集
        forbidden_end_pattern = r'[' + re.escape(forbidden_end_chars) + r']' if forbidden_end_chars else None
        
        # 找到子串在文本中的位置
        start_pos = text.find(substring)
        end_pos = start_pos + len(substring)
        
        # 向前扩展
        expanded_start = start_pos
        while expanded_start > 0:
            prev_char = text[expanded_start - 1]
            if re.match(allowed_chars, prev_char):
                # 检查是否违反首位约束
                if forbidden_start_pattern and re.match(forbidden_start_pattern, prev_char):
                    break
                expanded_start -= 1
            else:
                break
        
        # 向后扩展
        expanded_end = end_pos
        while expanded_end < len(text):
            next_char = text[expanded_end]
            if re.match(allowed_chars, next_char):
                # 检查是否违反末位约束
                if forbidden_end_pattern and re.match(forbidden_end_pattern, next_char):
                    break
                expanded_end += 1
            else:
                break
        
        return text[expanded_start:expanded_end]

    @staticmethod
    def is_alphanumeric(text: str) -> bool:
        """
        检测一个字符串仅由字母和数字构成
        """
        return bool(re.fullmatch(r'[a-zA-Z0-9]+', text))

    @staticmethod
    def is_substring_surrounded_by_non_custom(text: str, start, end, custom_chars: str = '') -> bool:
        """
        给定一个字符串和字符串的子串的start(index), end(index)，检测这个子串的左右两边不存在字母数字和自定义的字符
        """
        # 构建检测字符集
        check_chars = r'[a-zA-Z0-9' + re.escape(custom_chars) + r']'
        left_ok = (start == 0) or (not re.match(check_chars, text[start-1]))
        right_ok = (end == len(text)) or (not re.match(check_chars, text[end]) )
        return left_ok and right_ok

    def process(self, text: str) -> str:
        # 综合处理
        text = self.fullwidth_to_halfwidth(text)
        text = self.remove_non_breaking_spaces(text)
        text = self.to_lower(text)
        text = self.remove_invisible_chars(text)
        text = self.normalize_spaces(text)
        text = self.collapse_spaces(text)
        return text.strip() 
