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

prompts = [
    "Give me a very clear explanation of the core assertions, implications, and mechanics elucidated in this paper?",
    "Can you explain the value of this in basic terms? Like you're talking to a CEO. So what? What's the bottom line here?",
    "Can you give me an analogy or metaphor that will help explain this to a broad audience.",
]
default_max_chars = int(os.getenv('REDUCER_MAX_CHARS', 12000))
default_max_token_spend = int(os.getenv('REDUCER_MAX_TOKEN_SPEND', 12000))
default_model_engine = os.getenv('REDUCER_MODEL', "gpt-3.5-turbo-16k")
default_temperature = float(os.getenv('REDUCER_TEMPERATURE', 0.1))
default_personality = os.getenv('REDUCER_PERSONALITY', "You are a helpful AI assistant that is expert in taking in complex information and summarising it in a clear, friendly, concise accurate and informative way.")

def get_available_models():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    models = openai.Model.list()
    for model in models['data']:
        print(model.id)

def string_to_token_count(string, model_engine=default_model_engine):
    encoding = tiktoken.encoding_for_model(model_engine)
    return len(encoding.encode(string))

def get_token_price(model=default_model_engine, token_count=0, direction="output"):

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

def get_new_pdf_contents(papers_dir, max_chars=default_max_chars):
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

def call_openai_api(results, prompts, model_engine=default_model_engine, temperature=default_temperature, max_token_spend=default_max_token_spend, personality=default_personality):
    openai.api_key = os.environ["OPENAI_API_KEY"]
    api_responses = {}
    tokens_spent = 0
    for filename, contents in results.items():
        estimated_token_count = string_to_token_count(contents)
        print("Processing {} (estimated {} tokens)...".format(filename, estimated_token_count))
        combined_responses = []
        max_tries = 5
        try_count = 0
        for index, prompt in enumerate(prompts):
            messages = [
                {
                    'role': 'system',
                    'content': f"{personality}. Here is the text to summarise as instructed by the user: {contents}",
                },
                {
                    'role': 'user',
                    'content': prompt,
                }
            ]
            while try_count < max_tries:
                spinner = Halo(text=f'Thinking about prompt {index + 1}...', spinner='dots')
                spinner.start()
                try_count += 1
                try:
                    response = openai.ChatCompletion.create(
                        model=model_engine,
                        messages=messages,
                        temperature=temperature,
                    )
                    tokens = response['usage']['total_tokens']
                    print("Response received : tokens used: {} | Estimated cost US${}".format(tokens, get_token_price(model_engine, tokens, "output")))
                    tokens_spent += tokens
                    break
                except Exception as e:
                    print("Error calling OpenAI API: {}".format(e))
                    if try_count < max_tries:
                        print("Retrying in {} seconds...".format(try_count * 2))
                        sleep(try_count * 2)
                finally:
                    spinner.stop()
            if try_count >= max_tries:
                print("Failed to call OpenAI API after {} tries. Skipping {}.".format(max_tries, filename))
                break
            try_count = 0
            combined_responses.append("\n\n## Q. {}\n\n{}".format(prompt, response['choices'][0]['message']['content']))
        if len(combined_responses) > 0:
            api_responses[filename] = "# {}\n\n".format(filename) + '\n'.join(combined_responses)
        if max_token_spend > 0 and tokens_spent > max_token_spend:
            print(f"Max tokens ({max_token_spend}) exceeded. Skipping remaining files...")
            break
    return api_responses

# file operations
def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', action='store_true', help='List available OpenAI models')
    parser.add_argument('--url', help='URL of a webpage to summarise')
    args = parser.parse_args()

    # If the --models flag was passed, display the models available with the users API key
    if args.models:
        get_available_models()
        exit(0)

    # If the --url flag was passed, summarise the webpage
    if args.url:
        url = args.url
        results = {}
        filename = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
        filename = filename.replace(".", "_")
        filename = re.sub(r"/|_", "_", filename)
        filepath = os.path.join('papers', filename)
        if os.path.exists(filepath + '_summary.md'):
            print("Skipping {} as it has already been processed...".format(filename))
            exit(0)
        print("Summarising {}".format(url))
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text(strip=True)

        if default_max_chars > 0 and len(page_text) > int(default_max_chars):
            print("Truncating {} to {} characters...".format(filename, default_max_chars))
            text_contents = page_text[0:default_max_chars]
        results[filename] = page_text
        api_responses = call_openai_api(results, prompts)
        for filename, response in api_responses.items():
            filepath = os.path.join('papers', filename + '_summary.md')
            save_file(filepath, response)
        exit(0)
    papers_dir = 'papers'
    results = get_new_pdf_contents(papers_dir)
    api_responses = call_openai_api(results, prompts)
    for filename, response in api_responses.items():
        filepath = os.path.join(papers_dir, filename + '_summary.md')
        save_file(filepath, response)
