#!/usr/bin/env python3

import os
import PyPDF2
import openai
import argparse
from time import sleep
from halo import Halo
import tiktoken
import requests
from bs4 import BeautifulSoup
import re

# Defined as constants
MAX_TRIES = 5
PAPERS_DIR = 'papers'
# Use a configuration dictionary to manage settings
config = {
    "prompts": [
        "Give me a very clear explanation of the core assertions, implications, and mechanics elucidated in this paper?",
        "Can you explain the value of this in basic terms? Like you're talking to a CEO. So what? What's the bottom line here?",
        "Can you give me an analogy or metaphor that will help explain this to a broad audience.",
    ],
    "max_chars": int(os.getenv('REDUCER_MAX_CHARS', 12000)),
    "max_token_spend": int(os.getenv('REDUCER_MAX_TOKEN_SPEND', 12000)),
    "model_engine": os.getenv('REDUCER_MODEL', "gpt-3.5-turbo-16k"),
    "temperature": float(os.getenv('REDUCER_TEMPERATURE', 0.1)),
    "personality": os.getenv('REDUCER_PERSONALITY', "You are a helpful AI assistant that is expert in taking in complex information and summarising it in a clear, friendly, concise accurate and informative way.")
}

def get_available_models():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    models = openai.Model.list()
    for model in models['data']:
        print(model.id)

def string_to_token_count(string):
    encoding = tiktoken.encoding_for_model(config['model_engine'])
    return len(encoding.encode(string))

def get_token_price(model = config['model_engine'], token_count=0, direction="output"):
    if model.startswith('gpt-4-32k'):
        token_price_input = 0.03 / 1000
        token_price_output = 0.06 / 1000
    elif model.startswith('gpt-4'):
        token_price_input = 0.06 / 1000
        token_price_output = 0.12 / 1000
    elif model.startswith('gpt-3.5-turbo-16k'):
        token_price_input = 0.003 / 1000
        token_price_output = 0.004 / 1000
    elif model.startswith('gpt-3.5-turbo'):
        token_price_input = 0.0015 / 1000
        token_price_output = 0.002 / 1000
    else:
        token_price_input = 0.0
        token_price_output = 0.0

    if direction == "input":
        return round(token_price_input * token_count, 2)
    return round(token_price_output * token_count, 2)

def get_new_pdf_contents(papers_dir, max_chars=config['max_chars']):
    results = {}
    for filename in os.listdir(papers_dir):
        if filename.endswith('.pdf'):
            filepath = os.path.join(papers_dir, filename)
            if os.path.exists(filepath + '_summary.md'):
                print("Skipping {} as it has already been processed...".format(filename))
                continue
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_contents = ''
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_contents += page.extract_text()
                if max_chars > 0 and len(text_contents) > int(max_chars):
                    print("Truncating {} to {} characters...".format(filename, max_chars))
                    text_contents = text_contents[0:max_chars]
                results[filename] = text_contents
    return results

def call_openai_api(results: dict, config: dict) -> dict:
    """
    Calls the OpenAI API and returns the responses.

    Args:
        results: A dictionary with filename as key and contents as value.
        config: A dictionary with configurations.

    Returns:
        A dictionary with filename as key and API response as value.
    """
    openai.api_key = os.environ["OPENAI_API_KEY"]
    api_responses = {}
    tokens_spent = 0
    stop_processing = False
    for filename, contents in results.items():
        if stop_processing:
            break
        estimated_token_count = string_to_token_count(contents)
        print("Processing {} (estimated {} tokens)...".format(filename, estimated_token_count))
        combined_responses = []
        for index, prompt in enumerate(config["prompts"]):
            response, tokens = get_openai_response(contents, config, prompt, index)
            if response:
                combined_responses.append("\n\n## Q. {}\n\n{}".format(prompt, response['choices'][0]['message']['content']))
            tokens_spent += tokens
            if config["max_token_spend"] > 0 and tokens_spent > config["max_token_spend"]:
                print(f"Max tokens ({config['max_token_spend']}) exceeded. Skipping remaining files...")
                stop_processing = True
                break
        if combined_responses:
            api_responses[filename] = "# {}\n\n".format(filename) + '\n'.join(combined_responses)
    return api_responses

def get_openai_response(contents: str, config: dict, prompt: str, index: int) -> tuple:
    """
    Calls the OpenAI API with retry logic.

    Args:
        contents: The contents to summarize.
        config: A dictionary with configurations.
        prompt: The prompt to use.
        index: The index of the prompt.

    Returns:
        A tuple containing the response and tokens used.
    """
    messages = [
        {
            'role': 'system',
            'content': f"{config['personality']}. Here is the text to summarise as instructed by the user: {contents}",
        },
        {
            'role': 'user',
            'content': prompt,
        }
    ]
    for try_count in range(MAX_TRIES):
        spinner = Halo(text=f'Thinking about prompt {index + 1}...', spinner='dots')
        spinner.start()
        try:
            response = openai.ChatCompletion.create(
                model=config['model_engine'],
                messages=messages,
                temperature=config['temperature'],
            )
            tokens = response['usage']['total_tokens']
            print("Response received : tokens used: {} | Estimated cost US${}".format(tokens, get_token_price(config['model_engine'], tokens, "output")))
            return response, tokens
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            if try_count < MAX_TRIES - 1:
                print(f"Retrying in {try_count * 2} seconds...")
                sleep(try_count * 2)
        finally:
            spinner.stop()
    print("Failed to call OpenAI API after {} tries. Skipping {}.".format(MAX_TRIES, filename))
    return None, 0

def handle_webpage_summary(url: str, config: dict):
    """
    Handles the summarization of a webpage.

    Args:
        url: The URL of the webpage to summarize.
        config: A dictionary with configurations.
    """
    results = {}
    filename = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    filename = filename.replace(".", "_")
    filename = re.sub(r"/|_", "_", filename)
    filepath = os.path.join(PAPERS_DIR, filename)
    if os.path.exists(filepath + '_summary.md'):
        print("Skipping {} as it has already been processed...".format(filename))
        return
    print("Summarising {}".format(url))
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    page_text = soup.get_text(strip=True)

    if config["max_chars"] > 0 and len(page_text) > int(config["max_chars"]):
        print("Truncating {} to {} characters...".format(filename, config["max_chars"]))
        page_text = page_text[0:config["max_chars"]]
    results[filename] = page_text
    api_responses = call_openai_api(results, config)
    for filename, response in api_responses.items():
        filepath = os.path.join(PAPERS_DIR, filename + '_summary.md')
        save_file(filepath, response)

# file operations
def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', action='store_true', help='List available OpenAI models')
    parser.add_argument('--url', help='URL of a webpage to summarise')
    args = parser.parse_args()

    if args.models:
        get_available_models()
        exit(0)

    if args.url:
        handle_webpage_summary(args.url, config)
    else:
        results = get_new_pdf_contents(PAPERS_DIR, config["max_chars"])
        api_responses = call_openai_api(results, config)
        for filename, response in api_responses.items():
            filepath = os.path.join(PAPERS_DIR, filename + '_summary.md')
            save_file(filepath, response)
