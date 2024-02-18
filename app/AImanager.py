
import torch
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from conversation import Conversation

MODEL_NAME = "IlyaGusev/saiga_mistral_7b"
DEFAULT_MESSAGE_TEMPLATE = "<s>{role}\n{content}</s>"
DEFAULT_RESPONSE_TEMPLATE = "<s>bot\n"
DEFAULT_SYSTEM_PROMPT = "Ты — русскоязычный автоматический ассистент для помощи в подборе мероприятий. Ты разговариваешь с людьми и помогаешь им."


class AImanager:
    def __init__(self, mongo_ip="mongodb://mongodb:27017/") -> None:
        self.client = AsyncIOMotorClient(mongo_ip)
        self.collection = self.client["events_db"]["main"]
        
        config = PeftConfig.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            config.base_model_name_or_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.model = PeftModel.from_pretrained(
            model,
            MODEL_NAME,
            torch_dtype=torch.float16
        )

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
        self.generation_config = GenerationConfig.from_pretrained(MODEL_NAME)

    
    async def get_events_by_date_type(self, event_date, event_theme):
        filter = {"event.theme": {"$regex": event_theme}, "event.date": event_date}
        events = self.collection.find(filter)
        result = await events.to_list(length=None)
        return result
    
    def generate(self, prompt):
        data = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        data = {k: v.to(self.model.device) for k, v in data.items()}
        output_ids = self.model.generate(
            **data,
            generation_config=self.generation_config
        )[0]
        output_ids = output_ids[len(data["input_ids"][0]):]
        output = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        return output.strip()
    
    async def get_info(self, text):
        lines = text.split(';')
        date = lines[0].replace('дата: ', '')
        theme = lines[1].replace('тематика: ', '')
        event_lst = await self.get_events_by_date_type(date, theme)
        return event_lst
    

    async def process(self, text: str):
        self.conversation = Conversation(DEFAULT_MESSAGE_TEMPLATE, DEFAULT_SYSTEM_PROMPT, DEFAULT_RESPONSE_TEMPLATE)
        input_task = f"классифицируй этот запрос, сделанный к русскоязычному ассистенту: \"{text}\". Напиши, касается он посещения какого-то мероприятия, в ответ напиши только да или нет"
        self.conversation.add_user_message(input_task)
        prompt = self.conversation.get_prompt(self.tokenizer)
        output = self.generate(prompt)
        if output == "нет":
            return "Ваш запрос не касается помощи в подборе мероприятий. Такие запросы не обрабатываются"
        input_task = f"\
            проанализируй этот запрос, сделанный к русскоязычному ассистенту: \"{text}\".\
            найди в этом запросе дату,\
            среди тематик: развлечение концерт музыка саундтрек детям концерт выставка история культура искусство кинематограф современная музыка школа экономика классическая музыка орган выставка культура панк панк-выставка спектакль мюзикл концерт кино рок хип-хоп рэп соревнование конкурс итмо конференция конгресс ниоктр фестиваль драма\
            определи, к какой из них относится запрос, предоставь ответ в таком виде:\
            дата: ДД/ММ/ГГГГ;тематика: максимально близкая тематика"
        self.conversation.add_user_message(input_task)
        prompt = self.conversation.get_prompt(self.tokenizer)
        output = self.generate(prompt)
        event_lst = await self.get_info(output)
        event_text = "есть список мероприятий:\n"
        for event in event_lst:
            row = f"Название: {event['name']} Тип мероприятия: {event['type']} Описание: {event['description']} Дата: {event['date']} Время: {event['time']} Адрес: {event['address']} Ссылка на мероприятие: {event['href']} \n"
            event_text+=row
        event_text+="Среди этих мероприятий выбери максимально подходящие запросу пользователя и выведи в таком же виде, как они указаны в списке"
        self.conversation.add_user_message(event_text)
        prompt = self.conversation.get_prompt(self.tokenizer)
        output = self.generate(prompt)
        res = output+"Вот, что мне удалось найти по вашему запросу!\nРад, если в этом списке вы найдете то, что вам понравится.\nОбязательно оставьте отзыв после посещения мероприятия!"
        return res