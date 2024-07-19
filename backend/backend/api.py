from .enums import *
from .scripts import *

from ninja import NinjaAPI
import json
import pandas as pd

api = NinjaAPI()

@api.get("/test")
def test(request, llm: LLMEnum, judge: LLMEnum, copywriter: LLMEnum, category: int, google_search: bool = True, lang: LangEnum = LangEnum.ENGLISH, number: int = 4, version: int = 2):
    """
    **Perform testing of responses using Large Language Models (LLMs) for generating spec sheets.**

    **Args:**
    - `request`: The HTTP request object.
    - `llm` (LLMEnum): The LLM used to generate the spec sheets.
    - `judge` (LLMEnum): The LLM used to evaluate the generated spec sheets.
    - `copywriter` (LLMEnum): The LLM used to generate product descriptions.
    - `category` (int): The category ID of the products to be tested.
    - `google_search` (bool, optional): Whether to use Google search to gather additional context for the product queries. Defaults to True.
    - `lang` (LangEnum, optional): The language for the copywriter model. Defaults to LangEnum.ENGLISH.
    - `number` (int, optional): The prompt number for the "Maker" LLM. Defaults to 4.
    - `version` (int, optional): The prompt version for the "Maker" LLM. Defaults to 2.

    **Returns:**
    - `dict`: A dictionary containing the generated spec sheets, ground truth data, similarity scores, and LLM evaluations, serialized as JSON.
    """
    model = get_model(llm)
    judge_model = get_model(judge)
    copywriter_model = get_model(copywriter)
    
    model.start_chat(get_prompt("Maker",category, number, version))
    judge_model.start_chat(get_prompt("Judge",category, 1, 1))
    copywriter_model.start_chat(get_prompt("Copywriter",category, 1, 1, lang.value))

    df = pd.DataFrame(columns=["Spec Sheet", "Ground Truth", "Similarity Score", "LLM Evaluation"])
    for product in get_ground_truth(category):
        if google_search:
            prompt = search_google(product[0], model)
        else:
            prompt = product[0]
        response = model.send_message(prompt)
        try:
            raw_data = process_json(response)
            data = json.loads(raw_data)
            data['description'] = copywriter_model.send_message(raw_data)
            df.loc[-1] = evaluate(data,product[1], judge_model)
            df.index = df.index + 1
            df = df.sort_index()

        except json.JSONDecodeError:
            df.loc[-1] = [response,product[1].to_json(),{"veredict":None,"score":None},{"veredict":None,"reasoning":None}]
            df.index = df.index + 1
            df = df.sort_index()
    return json.loads(df.to_json())

@api.get("/categories")
def categories(request):
    """
    **Retrieves a list of all available categories.**

    **Returns:**
    - `list`: A list of dictionaries, where each dictionary contains the following keys:
        - `id`: The ID of the category.
        - `name`: The name of the category.
    """
    return get_category_list()

@api.get("/prompts")
def prompts(request, role: RoleEnum):
    """
    **Retrieves a list of prompts based on the specified role.**

    **Args:**
    - `request`: The request object.
    - `role` (RoleEnum): The role for which prompts are retrieved.

    **Returns:**
    - `list`: A list of dictionaries, where each dictionary contains the following keys:
        - `category`: The name of the category the prompt belongs to.
        - `lang`: The language of the prompt.
        - `number`: The number of the prompt.
        - `version`: The version of the prompt.
        - `content`: The textual content of the prompt.
    """
    return get_prompt_list(role)

@api.post("/get_sheets")
def get_sheets(request, products: list[str], llm: LLMEnum, copywriter: LLMEnum, category: int, google_search: bool = True, number: int = 4, version: int = 2):
    """
    **Generates spec sheets for the given list of products using Large Language Models (LLMs).**

    **Args:**
    - `request`: The request object.
    - `products` (list[str]): A list of product names for which spec sheets are generated.
    - `llm` (LLMEnum): The LLM to use for generating spec sheets.
    - `copywriter` (LLMEnum): The LLM to use for generating copywriting responses.
    - `category` (int): The category ID for the products.
    - `google_search` (bool, optional): Whether to perform Google search to gather context for product queries. Defaults to True.
    - `number` (int, optional): The number of the prompt for the Maker LLM. Defaults to 4.
    - `version` (int, optional): The version of the prompt for the Maker LLM. Defaults to 2.

    **Returns:**
    - `list`: A list of dictionaries representing the generated spec sheets for the products.
        Each dictionary contains information about the product, including its spec sheet and description.
    """
    res = []
    model = get_model(llm)
    copywriter_model = get_model(copywriter)

    model.start_chat(get_prompt("Maker",category, number, version))
    copywriter_model.start_chat(get_prompt("Copywriter",category, 1, 1))
    for product in products:
        if google_search:
            prompt = search_google(product, model)
        else:
            prompt = product
        response = model.send_message(prompt)
        try:
            raw_data = process_json(response)
            data = json.loads(raw_data)
            data['description'] = copywriter_model.send_message(raw_data)
            res.append(data)
        except json.JSONDecodeError:
            res.append(response)
    return res
