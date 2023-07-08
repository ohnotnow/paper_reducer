# Paper Reducer

This script uses OpenAI's GPT API to generate multiple summaries of research papers in response to differing prompts. It is designed to work with PDF files and outputs the summaries in Markdown format.

## Installation

1. Clone this repository to your local machine.
2. Navigate to the cloned repository in your terminal or command prompt.
3. Create a virtual environment (optional but recommended).
4. Install the required packages by running the following command:
```sh
pip install -r requirements.txt
```
Note that you may need to use `pip3` instead of `pip` depending on your Python installation.

## Usage

1. Place your PDF files in the `papers` directory.
2. Run the script by executing the following command (you will need your OpenAI API key - see [OpenAI's API docs](https://platform.openai.com/account/api-keys) if you don't have one):
```sh
export OPENAI_API_KEY=sk-......
python3 paper_reducer.py
```
3. The script will generate summary files in Markdown format for each PDF file in the `papers` directory.

Note - again depending on your python install you might have to run `python` or `python3`.

## Customisation
### Prompts
The script uses a set of default prompts to generate summaries of research papers. If you would like to change the prompts or add your own, you can modify the prompts list in the `paper_reducer.py` script. They are defined in the `prompts` array near the top of the script.

### OpenAI Model
By default, this script uses the `gpt-3.5-turbo-16k` model from OpenAI's API. If you have access to other models and would like to use them instead, you can change the model variable in the paper_reducer.py script to the name of the model you want to use.
```python
api_responses = call_openai_api(results, prompts, model_engine="a_different_openai_model")
```

### Maximum spend
The script is quite conservative by default and has a max token spend of 10000 (at the time of writing - should be around US$0.30).  If you want to process more than one or two papers at one time, you probably want to increase that to 20000+.  (For reference - a fairly average Arxiv pdf uses about 3.5k tokens).
```python
api_responses = call_openai_api(results, prompts, max_token_spend=40000)
```

### Maximum characters to send to OpenAI
By default the script limits the size of text from a paper to 12000 characters so as not to risk hitting limits.  If you are using a larger models like `gpt-4-32k` then you can up the limit.
```python
results = get_new_pdf_contents(papers_dir, max_chars=30000)
```
## Requirements

* An OpenAI API key.
* Python3 with the packages - PyPDF2, openai, halo

## Credits

Inspired on the back of watching a youtube video by [David Shapiro](https://www.youtube.com/@DavidShapiroAutomator).  And written before I realised he had pushed his own code upto GitHub which would have saved me the effort.
