from django.conf import settings
from .enums import LLMEnum
from specgenie.models import Category, PromptRole, PromptLang, Prompt, GroundTruthProduct
import google.generativeai as genai
from openai import OpenAI
from thefuzz import fuzz
import json, requests, time, tiktoken
from bs4 import BeautifulSoup

def get_category_list():
  """
  Retrieves a list of all available categories from the database.

  **Returns:**
  - `list`: A list of dictionaries, where each dictionary contains the following keys:
      - `id`: The ID of the category.
      - `name`: The name of the category.
  """
  res = [{'id': category.id, 'name': category.name} for category in Category.objects.all()]
  return res

def get_prompt_list(role):
  """
  **Retrieves a list of prompts based on the specified role.**

  **Args:**
  - `role`: The role for which prompts are retrieved.

  **Returns:**
  - `list`: A list of dictionaries, where each dictionary contains the following keys:
      - `category`: The name of the category the prompt belongs to.
      - `lang`: The language of the prompt.
      - `number`: The number of the prompt.
      - `version`: The version of the prompt.
      - `content`: The textual content of the prompt.
  """
  desired_role = PromptRole.objects.get(name=role)
  res = [{"category":prompt.category.name, "lang":prompt.lang.name,"number": prompt.number, "version": prompt.version, "content":prompt.content} for prompt in Prompt.objects.filter(role=desired_role)]
  return res

def get_prompt(role,category, number, version, lang = "en"):
  """
  **Retrieves a specific prompt based on the provided parameters.**

  **Args:**
  - `role`: The role of the prompt.
  - `category`: The ID of the category to which the prompt belongs.
  - `number`: The number of the prompt.
  - `version`: The version of the prompt.
  - `lang` (optional): The language of the prompt. Defaults to "en".

  **Returns:**
  - `str`: The textual content of the prompt.
  """
  desired_role = PromptRole.objects.get(name=role)
  desired_lang = PromptLang.objects.get(name=lang)
  desired_category = Category.objects.get(id=category)
  prompt = Prompt.objects.get(category=desired_category, role=desired_role, lang=desired_lang, number=number, version=version)
  return prompt.content

def get_ground_truth(category):
  """
  **Retrieves a list of ground truth products for the specified category.**

  **Args:**
  - `category`: The ID of the category for which ground truth products are retrieved.

  **Returns:**
  - `list`: A list of tuples, where each tuple contains the product name and its corresponding GroundTruthProduct object.
  """
  res = []
  desired_category = Category.objects.get(id=category)
  product_list = GroundTruthProduct.objects.filter(category=desired_category)
  for product in product_list:
    res.append((f"{product.brand} {product.part_number}",product))
  return res

def process_json(data):
  """
  **Processes a LLM's response to ensure proper JSON formatting.**

  **Args:**
  - `data` (str): The JSON data to be processed.

  **Returns:**
  - `str`: The processed JSON data.
  """
  try:
    start_index = data.find("{")
    end_index = data.rfind("}")

    if start_index != -1 and end_index > start_index:
      data = data[start_index:end_index + 1]
  except Exception as e:
    pass
  return data

class GeminiAPI:
  """
  This class encapsulates functionalities related to interacting with the Gemini API.
  """
  def __init__(self,gmodel='gemini-pro'):
    """
    **Initializes a new instance of the GeminiAPI class.**

    **Args:**
    - `gmodel` (str, optional): The name of the GPT model to use. Defaults to 'gemini-pro'.
    """
    genai.configure(api_key=settings.API_KEY_GEMINI)
    self.model = genai.GenerativeModel(gmodel)
    self.tokens = 0
    self.max_tokens = 20000
    self.token_limit_per_min = 30000
    self.tokens_used_this_minute = 0
    self.last_request_time = time.time()
  def start_chat(self,prompt):
    """
    Starts a new chat session with the Gemini API.

    Returns:
      A reference to the chat object for further interactions.
    """
    for attempt in range(settings.ATTEMPTS_PER_MESSAGE):
      try:
        self.chat = self.model.start_chat(history=[])
        self.response = self.chat.send_message(prompt)
        self.tokens += self.count_tokens(prompt)
        return self.response.text
      except Exception as e:
        if attempt < settings.ATTEMPTS_PER_MESSAGE - 1:
          wait_time = settings.WAIT_TIME * 3 ** attempt
          time.sleep(wait_time)
        else:
          return f"An error occurred while communicating with Gemini.\nError: {e}"
  def send_message(self, message):
    """
    **Sends a message in the current chat session with the Gemini API.**

    **Args:**
    - `message` (str): The message to send.

    **Returns:**
    - `str`: The response text from the API.
    """
    for attempt in range(settings.ATTEMPTS_PER_MESSAGE):
      try:
        # Check if tokens per minute limit is exceeded
        current_time = time.time()
        if self.tokens_used_this_minute > self.token_limit_per_min:
          time_to_wait = 60 - (current_time - self.last_request_time)
          time.sleep(time_to_wait)
          self.tokens_used_this_minute = 0
        self.last_request_time = time.time()
        self.response = self.chat.send_message(message)
        self.tokens += self.count_tokens(message)
        return self.response.text
      except Exception as e:
        if attempt < settings.ATTEMPTS_PER_MESSAGE - 1:
          wait_time = settings.WAIT_TIME * 2 ** attempt
          time.sleep(wait_time)
        else:
          pass
          return f"An error occurred while communicating with Gemini.\nError: {e}"
  def count_tokens(self, prompt):
     """
    **Counts the number of tokens in a prompt.**

    **Args:**
    - `prompt` (str): The prompt to count tokens for.

    **Returns:**
    - `int`: The number of tokens in the prompt.
    """
     return self.model.count_tokens(prompt).total_tokens
  def clear_history(self):
    """
    **Clears the chat history and token count.**
    """
    self.tokens = 0
    self.start_chat(self.chat.history[0].parts[0].text)
  
class ChatGPTAPI:
    """
    This class encapsulates functionalities related to interacting with the ChatGPT API.
    """
    def __init__(self, gmodel='gpt-4o'):
        """
        Initializes a new instance of the ChatGPTAPI class.
        
        Args:
        - gmodel (str, optional): The name of the GPT model to use. Defaults to 'gpt-4o'.
        """
        self.client = OpenAI(api_key=settings.API_KEY_OPENAI)
        self.model = gmodel
        self.messages = []
        self.tokens = 0
        self.max_tokens = 20000
        self.token_limit_per_min = 30000
        self.tokens_used_this_minute = 0
        self.last_request_time = time.time()

    def start_chat(self, prompt):
        """
        Starts a new chat session with the ChatGPT API.
        
        Args:
        - prompt (str): The initial prompt to start the chat session.
        """
        self.messages.append({"role": "system", "content": prompt})
        self.tokens += self.count_tokens(prompt)

    def send_message(self, message):
        """
        Sends a message to the ChatGPT API and retrieves the response.
        
        Args:
        - message (str): The message to send to the API.
        
        Returns:
        - str: The response message from the API.
        """
        try:
            self.messages.append({"role": "user", "content": message})
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            self.messages.append(response.choices[0].message)
            self.tokens += self.count_tokens(message)
            self.tokens_used_this_minute += self.count_tokens(message) + self.count_tokens(response.choices[0].message.content)
            
            # Check if tokens per minute limit is exceeded
            current_time = time.time()
            if self.tokens_used_this_minute > self.token_limit_per_min:
                time_to_wait = 60 - (current_time - self.last_request_time)
                time.sleep(time_to_wait)
                self.tokens_used_this_minute = 0
            self.last_request_time = time.time()
                
            return response.choices[0].message.content
        
        except Exception as e:
            pass
            return f"An error occurred while communicating with GPT.\nError: {e}"

    def count_tokens(self, prompt):
        """
        Counts the number of tokens in a prompt.
        
        Args:
        - prompt (str): The prompt to count tokens for.
        
        Returns:
        - int: The number of tokens in the prompt.
        """
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            encoding = tiktoken.get_encoding("o200k_base")
        return len(encoding.encode(prompt))

    def clear_history(self):
        """
        Clears the chat history and token count.
        """
        starting_prompt = self.messages[0]
        self.messages = [starting_prompt]
        self.tokens = self.count_tokens(starting_prompt['content'])
def get_model(llm):
  """
  **Returns an instance of the specified Large Language Model (LLM).**

  **Args:**
  - `llm` (LLMEnum): The enum representing the desired LLM.

  **Returns:**
  - `object`: An instance of the specified LLM class.
  """
  if llm == LLMEnum.GEMINI:
    model = GeminiAPI()
  elif llm == LLMEnum.CHATGPT:
    model = ChatGPTAPI()
  #add more models if needed here

  return model
  
def evaluate(response, product, model):
  """
  **Evaluates the response generated by an LLM for a given product against its ground truth.**

  **Args:**
  - `response` (dict): The response generated by the LLM.
  - `product` (GroundTruthProduct): The ground truth product against which the response is evaluated.
  - `model`: The LLM used to generate evaluate the response.

  **Returns:**
  - `list`: A list containing the response, ground truth, similarity score, and LLM evaluation results.
      - `response` (dict): The response generated by the LLM.
      - `ground_truth` (dict): The ground truth attributes of the product.
      - `similarity_score` (dict): The similarity score indicating the correctness of the response.
      - `llm_evaluation` (dict): The evaluation of the response by the LLM.
  """
  ground_truth = product.to_json()
  similarities = []

  for key in ground_truth.keys():
    if key in response and key != 'description':
      similarities.append(fuzz.ratio(response[key], ground_truth[key]))
  average = sum(similarities)/len(similarities)
  if average < 50:
    similarity_score = {"veredict":"Incorrect","score":average}
  elif average < 80:
    similarity_score = {"veredict":"Inconsistencies found","score":average}
  else:
    similarity_score = {"veredict":"Correct","score":average}

  ground_truth_no_desc = {key: value for key, value in ground_truth.items() if key != 'description'}
  response_no_desc = {key: value for key, value in response.items() if key != 'description'}
  llm_evaluation = model.send_message(f"{ground_truth_no_desc}\n{response_no_desc}")

  try:
    llm_evaluation = json.loads(process_json(llm_evaluation))
  except json.JSONDecodeError:
    llm_evaluation = {"veredict":None,"reasoning":llm_evaluation}
  return [response,ground_truth,similarity_score,llm_evaluation]

def build_payload(key,id,query,start=1,num=10):
  """
  **Builds a payload for making requests to the Google Custom Search API.**

  **Args:**
  - `key` (str): The API key for accessing the Google Custom Search API.
  - `id` (str): The identifier for the custom search engine.
  - `query` (str): The search query.
  - `start` (int, optional): The index of the first result to return. Defaults to 1.
  - `num` (int, optional): The number of results to return. Defaults to 10.

  **Returns:**
  - `dict`: A dictionary containing the payload for the API request.
  """
  payload = {
    'key':key,
    'q':query,
    'cx':id,
    'start':start,
    'num':num
  }
  return payload

def search_google(product, model):
  """
  **Searches Google for information related to the given product and generates a prompt for the LLM based on the search results.**

  **Args:**
  - `product` (str): The product to search for.
  - `model`: The LLM used for generating prompts.

  **Returns:**
  - `str`: A prompt generated based on the search results.
  """
  i = 0
  while True:
    results = requests.get(
      'https://customsearch.googleapis.com/customsearch/v1',
      params=build_payload(
        settings.API_KEY_CSE,
        settings.SEARCH_ENGINE_ID,
        product,
        1+i*10)).json()
    items = results['items']
    for item in items:
      try:
        response = requests.get(item['link'], timeout=5)
        if response.status_code == 200:
          soup = BeautifulSoup(response.text, 'html.parser')
          prompt = f"<context>{soup.get_text().replace("\n\n\n\n","\n")}</context>\n{product}"
          tokens = model.count_tokens(prompt)
          if model.max_tokens > tokens:
            if tokens+model.tokens >= model.max_tokens:
              model.clear_history()
            return prompt
          else:
            pass
        else:
          pass
      except Exception as e:
        pass
    i += 1