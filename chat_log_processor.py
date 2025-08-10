import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
import argparse
import os

class ChatLogProcessor:
    def __init__(self, max_rounds: int = 3):
        """
        初始化聊天日志处理器
        
        Args:
            max_rounds: 最大轮数，默认为3轮
        """
        self.max_rounds = max_rounds
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        加载Excel数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            加载的数据框
        """
        try:
            df = pd.read_excel(file_path)
            print(f"成功加载数据，共 {len(df)} 条记录")
            return df
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None
    
    def validate_columns(self, df: pd.DataFrame) -> bool:
        """
        验证数据列是否存在
        
        Args:
            df: 数据框
            
        Returns:
            是否验证通过
        """
        required_columns = ['session_id', 'question_content', 'answer_content', 'create_time', 'user_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"缺少必需的列: {missing_columns}")
            return False
        
        print("数据列验证通过")
        return True
    
    def sort_by_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        按时间排序
        
        Args:
            df: 数据框
            
        Returns:
            排序后的数据框
        """
        # 确保create_time是datetime类型
        df['create_time'] = pd.to_datetime(df['create_time'])
        
        # 按session_id和create_time排序
        df_sorted = df.sort_values(['session_id', 'create_time']).reset_index(drop=True)
        print("数据已按时间排序")
        return df_sorted
    
    def process_session(self, session_data: pd.DataFrame) -> List[Dict]:
        """
        处理单个session的数据
        
        Args:
            session_data: 单个session的数据
            
        Returns:
            处理后的数据列表
        """
        results = []
        session_id = session_data['session_id'].iloc[0]
        user_name = session_data['user_name'].iloc[0]
        
        # 获取所有轮次的数据
        rounds = []
        for _, row in session_data.iterrows():
            rounds.append({
                'question': row['question_content'],
                'answer': row['answer_content']
            })
        
        # 生成滑动窗口数据
        for i in range(len(rounds)):
            # 当前轮次
            current_round = rounds[i]
            
            # 上一轮问题（如果存在）
            prev_question = rounds[i-1]['question'] if i > 0 else ""
            
            # 上一轮答案（如果存在）
            prev_answer = rounds[i-1]['answer'] if i > 0 else ""
            
            # 本轮问题
            current_question = current_round['question']
            
            # 添加到结果中
            results.append({
                '上轮问题': prev_question,
                '上轮答案': prev_answer,
                '本轮问题': current_question,
                'session_id': session_id,
                'user_name': user_name
            })
        
        return results
    
    def process_all_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理所有session的数据
        
        Args:
            df: 原始数据框
            
        Returns:
            处理后的数据框
        """
        all_results = []
        
        # 按session_id分组处理
        for session_id, session_data in df.groupby('session_id'):
            session_results = self.process_session(session_data)
            all_results.extend(session_results)
        
        # 转换为DataFrame
        result_df = pd.DataFrame(all_results)
        
        print(f"处理完成，共生成 {len(result_df)} 条标注数据")
        return result_df
    
    def filter_by_rounds(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据最大轮数过滤数据
        
        Args:
            df: 处理后的数据框
            
        Returns:
            过滤后的数据框
        """
        # 统计每个session的轮数
        session_rounds = df.groupby('session_id').size()
        
        # 过滤出轮数不超过max_rounds的session
        valid_sessions = session_rounds[session_rounds <= self.max_rounds].index
        filtered_df = df[df['session_id'].isin(valid_sessions)]
        
        print(f"过滤后剩余 {len(filtered_df)} 条数据，涉及 {len(valid_sessions)} 个session")
        return filtered_df
    
    def save_data(self, df: pd.DataFrame, output_path: str):
        """
        保存处理后的数据
        
        Args:
            df: 要保存的数据框
            output_path: 输出文件路径
        """
        try:
            df.to_excel(output_path, index=False)
            print(f"数据已保存到: {output_path}")
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def generate_statistics(self, df: pd.DataFrame):
        """
        生成数据统计信息
        
        Args:
            df: 数据框
        """
        print("\n=== 数据统计信息 ===")
        print(f"总数据条数: {len(df)}")
        print(f"涉及session数: {df['session_id'].nunique()}")
        print(f"涉及用户软件数: {df['user_name'].nunique()}")
        
        # 统计空值情况
        print("\n空值统计:")
        for col in ['上轮问题', '上轮答案', '本轮问题']:
            empty_count = (df[col] == "").sum()
            print(f"{col}: {empty_count} 条空值")
        
        # 统计问题长度分布
        print("\n问题长度统计:")
        question_lengths = df['本轮问题'].str.len()
        print(f"平均长度: {question_lengths.mean():.2f}")
        print(f"最短长度: {question_lengths.min()}")
        print(f"最长长度: {question_lengths.max()}")
        
        # 按软件统计
        print("\n按软件统计:")
        software_stats = df['user_name'].value_counts()
        for software, count in software_stats.items():
            print(f"{software}: {count} 条")
    
    def process(self, input_path: str, output_path: str, filter_rounds: bool = True):
        """
        完整的处理流程
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            filter_rounds: 是否按轮数过滤
        """
        print("开始处理聊天日志数据...")
        
        # 1. 加载数据
        df = self.load_data(input_path)
        if df is None:
            return
        
        # 2. 验证列
        if not self.validate_columns(df):
            return
        
        # 3. 排序
        df = self.sort_by_time(df)
        
        # 4. 处理所有session
        result_df = self.process_all_sessions(df)
        
        # 5. 按轮数过滤（可选）
        if filter_rounds:
            result_df = self.filter_by_rounds(result_df)
        
        # 6. 生成统计信息
        self.generate_statistics(result_df)
        
        # 7. 保存数据
        self.save_data(result_df, output_path)
        
        print("处理完成！")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='处理智能客服日志数据')
    parser.add_argument('input_file', help='输入Excel文件路径')
    parser.add_argument('output_file', help='输出Excel文件路径')
    parser.add_argument('--max_rounds', type=int, default=3, help='最大轮数（默认3）')
    parser.add_argument('--no_filter', action='store_true', help='不按轮数过滤')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"输入文件不存在: {args.input_file}")
        return
    
    # 创建处理器
    processor = ChatLogProcessor(max_rounds=args.max_rounds)
    
    # 处理数据
    processor.process(
        input_path=args.input_file,
        output_path=args.output_file,
        filter_rounds=not args.no_filter
    )

if __name__ == "__main__":
    # 如果直接运行，使用示例参数
    if len(os.sys.argv) == 1:
        print("使用示例:")
        print("python chat_log_processor.py input.xlsx output.xlsx")
        print("python chat_log_processor.py input.xlsx output.xlsx --max_rounds 5")
        print("python chat_log_processor.py input.xlsx output.xlsx --no_filter")
    else:
        main() 