import json

class SystemConfig:
    def __init__(self, config_file='esg_news_system.json'):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def get_gemini_prompt(self, company, year):
        # 從 JSON 讀取 prompt 模板
        template = self.config['workflow']['step_2_gemini_task']['prompt_template']['user']
        return template.replace('{company_name}', company).replace('{year}', str(year))
    
    def get_timeout(self):
        return self.config['error_handling']['global_timeout']