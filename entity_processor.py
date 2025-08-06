from text_processor import TextProcessor
from typing import List, Dict, Optional, Tuple

class EntityProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def preprocess_query(self, query: str) -> str:
        """
        对输入query进行预处理
        """
        return self.text_processor.process(query)
    
    def recognize_entities(self, processed_query: str) -> List[Dict]:
        """
        实体识别方法（待实现）
        
        Args:
            processed_query: 预处理后的查询字符串
            
        Returns:
            实体列表，每个实体包含以下信息：
            {
                'text': '实体文本',
                'start_index': 开始位置,
                'end_index': 结束位置,
                'type': '实体类型'  # 可选
            }
        """
        # TODO: 实现实体识别逻辑
        # 示例返回格式：
        # return [
        #     {'text': 'entity1', 'start_index': 0, 'end_index': 7, 'type': 'PERSON'},
        #     {'text': 'entity2', 'start_index': 10, 'end_index': 16, 'type': 'ORG'}
        # ]
        return []
    
    def correct_entity(self, original_entity: str, expanded_entity: str, 
                      start_index: int, end_index: int) -> Optional[Dict]:
        """
        实体纠错方法（待实现）
        
        Args:
            original_entity: 原始实体文本
            expanded_entity: 扩展后的实体文本
            start_index: 开始位置
            end_index: 结束位置
            
        Returns:
            纠错后的实体信息，如果不需要纠错则返回None
        """
        # TODO: 实现纠错逻辑
        # 示例返回格式：
        # return {
        #     'text': 'corrected_entity',
        #     'start_index': start_index,
        #     'end_index': end_index,
        #     'type': 'entity_type'
        # }
        return None
    
    def expand_entity_without_overlap(self, query: str, entity: Dict, 
                                    all_entities: List[Dict], custom_chars: str = '',
                                    forbidden_start_chars: str = '', 
                                    forbidden_end_chars: str = '') -> str:
        """
        对实体进行补全，确保补全后的index不与其他实体重合
        
        Args:
            query: 原始查询字符串
            entity: 当前实体信息
            all_entities: 所有实体列表
            custom_chars: 自定义字符
            forbidden_start_chars: 不能出现在首位的字符
            forbidden_end_chars: 不能出现在末位的字符
            
        Returns:
            补全后的实体文本
        """
        # 获取当前实体的位置信息
        current_start = entity['start_index']
        current_end = entity['end_index']
        entity_text = entity['text']
        
        # 找到其他实体的边界
        other_boundaries = []
        for other_entity in all_entities:
            if other_entity != entity:
                other_boundaries.append((other_entity['start_index'], other_entity['end_index']))
        
        # 使用expand_substring进行补全
        expanded_text = self.text_processor.expand_substring(
            query, entity_text, custom_chars, forbidden_start_chars, forbidden_end_chars
        )
        
        # 找到扩展后文本在原始查询中的位置
        expanded_start = query.find(expanded_text)
        expanded_end = expanded_start + len(expanded_text)
        
        # 检查是否与其他实体重叠
        for start, end in other_boundaries:
            if (expanded_start < end and expanded_end > start):
                # 有重叠，返回原始实体
                return entity_text
        
        return expanded_text
    
    def detect_potential_entities(self, query: str, custom_chars: str = '',
                                start_constraint: bool = False, 
                                end_constraint: bool = False) -> List[Dict]:
        """
        使用detect_continuous_custom_chars检测潜在实体
        
        Args:
            query: 查询字符串
            custom_chars: 自定义字符
            start_constraint: 首位约束
            end_constraint: 末位约束
            
        Returns:
            潜在实体列表
        """
        potential_entities = self.text_processor.detect_continuous_custom_chars(
            query, custom_chars, start_constraint, end_constraint
        )
        
        entities = []
        for entity_text in potential_entities:
            start_index = query.find(entity_text)
            end_index = start_index + len(entity_text)
            entities.append({
                'text': entity_text,
                'start_index': start_index,
                'end_index': end_index,
                'type': 'DETECTED'
            })
        
        return entities
    
    def process_query(self, query: str, custom_chars: str = '',
                     forbidden_start_chars: str = '', forbidden_end_chars: str = '',
                     start_constraint: bool = False, end_constraint: bool = False) -> List[Dict]:
        """
        主要的处理流程
        
        Args:
            query: 输入查询
            custom_chars: 自定义字符
            forbidden_start_chars: 不能出现在首位的字符
            forbidden_end_chars: 不能出现在末位的字符
            start_constraint: 首位约束
            end_constraint: 末位约束
            
        Returns:
            处理后的实体列表
        """
        # 1. 预处理
        processed_query = self.preprocess_query(query)
        
        # 2. 实体识别
        entities = self.recognize_entities(processed_query)
        
        # 3. 处理识别到的实体
        if entities:
            # 按start_index排序
            entities.sort(key=lambda x: x['start_index'])
            
            final_entities = []
            for entity in entities:
                # 对每个实体进行补全
                expanded_text = self.expand_entity_without_overlap(
                    processed_query, entity, entities, custom_chars,
                    forbidden_start_chars, forbidden_end_chars
                )
                
                # 检查补全后的实体是否与源实体一致
                if expanded_text == entity['text']:
                    # 一致，沿用当前实体
                    final_entities.append(entity)
                else:
                    # 不一致，进行纠错
                    corrected_entity = self.correct_entity(
                        entity['text'], expanded_text,
                        entity['start_index'], entity['end_index']
                    )
                    
                    if corrected_entity:
                        # 纠错有返回，使用纠错后的实体
                        final_entities.append(corrected_entity)
                    else:
                        # 纠错没有返回，使用源实体
                        final_entities.append(entity)
            
            return final_entities
        
        else:
            # 4. 没有识别到实体，使用detect_continuous_custom_chars
            potential_entities = self.detect_potential_entities(
                processed_query, custom_chars, start_constraint, end_constraint
            )
            
            final_entities = []
            for entity in potential_entities:
                # 对每个潜在实体进行补全
                expanded_text = self.expand_entity_without_overlap(
                    processed_query, entity, potential_entities, custom_chars,
                    forbidden_start_chars, forbidden_end_chars
                )
                
                # 检查补全后的实体是否与源实体一致
                if expanded_text == entity['text']:
                    # 一致，沿用当前实体
                    final_entities.append(entity)
                else:
                    # 不一致，进行纠错
                    corrected_entity = self.correct_entity(
                        entity['text'], expanded_text,
                        entity['start_index'], entity['end_index']
                    )
                    
                    if corrected_entity:
                        # 纠错有返回，使用纠错后的实体
                        final_entities.append(corrected_entity)
                    else:
                        # 纠错没有返回，使用源实体
                        final_entities.append(entity)
            
            return final_entities 