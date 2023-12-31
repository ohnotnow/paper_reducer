# Paper Reducer

This script uses OpenAI's GPT API to generate multiple summaries of research papers in response to differing prompts. It is designed to work with PDF files and outputs the summaries in Markdown format.
You can see some example output towards the bottom of this readme.

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

You can also pass the url to a regular webpage (not a file/pdf/docx yet though) :
```sh
export OPENAI_API_KEY=sk-....
python3 paper_reducer.py --url=https://www.example.com/page.html
```
## Customisation
### Prompts
The script uses a set of default prompts to generate summaries of research papers. If you would like to change the prompts or add your own, you can modify the prompts list in the `paper_reducer.py` script. They are defined in the `prompts` array near the top of the script.

### OpenAI Model
By default, this script uses the `gpt-3.5-turbo-16k` model from OpenAI's API. If you have access to other models and would like to use them instead, you can change the model variable in the paper_reducer.py script to the name of the model you want to use.
```python
default_model_engine = os.getenv('REDUCER_MODEL', "gpt-3.5-turbo-16k")
```
If you don't know which models you have available for your API key - then you can run the script with `--models` after it and it'll print out all that are open to you.  Generally you're looking for the `gpt-*` ones.

### Maximum spend
The script is quite conservative by default and has a max token spend of 12000 (at the time of writing - should be around US$0.02 using gpt-3, US$0.90 for gpt-4 (*I think* - I wish they had a token/spend calculator)).  If you want to process more than one or two papers at one time, you probably want to increase that to 20000+.  (For reference - a fairly average Arxiv pdf uses about 3.5k tokens per prompt/summary).
```python
default_max_token_spend = os.getenv('REDUCER_MAX_TOKEN_SPEND', 12000)
```
If you set this to 0 then there is no maximum.
### Maximum characters to send to OpenAI
By default the script limits the size of text from a paper to 12000 characters (roughly 3000 tokens) so as not to risk hitting limits.  If you are using a larger models like `gpt-4-32k` then you can up the limit.  (It's worth doing a character count on some papers to check what suits your situation).
```python
default_max_chars = os.getenv('REDUCER_MAX_CHARS', 12000)
```
If you set this to 0 then there is no maximum.
### Creativity
The script defaults to being quite 'straight down the line' in it's calls to the API's and uses a temperature of 0.1.  If you want the models to be more 'creative' you can change the temperature (range is from 0 to 2).
```python
default_temperature = os.getenv('REDUCER_TEMPERATURE', 0.1)
```

### Personality
The script gives the model a little additional information to let it know it's "role" and help shape the responses.  You can change those to suit your circumstances.
```python
default_personality = os.getenv('REDUCER_PERSONALITY', "You are a helpful AI assistant that is expert in taking in complex information and summarising it in a clear, friendly, concise accurate and informative way.")
```

### Example cost of running against three Arxiv papers
With the `REDUCER_MODEL` set to the default 'gpt-3.5-turbo-16k', the `REDUCER_MAX_CHARS` set to 40000 (to fit in gpt-3.5's token limit) and `REDUCER_MAX_TOKEN_SPEND` set to '0' (infinite) then we can see estimated costs :
```sh
$ python3 paper_reducer.py
Truncating 2307.02564.pdf to 40000 characters...
Processing 2307.02564.pdf (estimated 13541 tokens)...
⠸ Thinking about prompt 1...Response received : tokens used: 13930 | Estimated cost US$0.06
⠇ Thinking about prompt 2...Response received : tokens used: 13845 | Estimated cost US$0.06
⠼ Thinking about prompt 3...Response received : tokens used: 13860 | Estimated cost US$0.06
Processing 2307.02496.pdf (estimated 5455 tokens)...
⠋ Thinking about prompt 1...Response received : tokens used: 5814 | Estimated cost US$0.02
⠹ Thinking about prompt 2...Response received : tokens used: 5664 | Estimated cost US$0.02
⠧ Thinking about prompt 3...Response received : tokens used: 5794 | Estimated cost US$0.02
Processing 2307.02486.pdf (estimated 10325 tokens)...
⠧ Thinking about prompt 1...Response received : tokens used: 10807 | Estimated cost US$0.04
⠼ Thinking about prompt 2...Response received : tokens used: 10548 | Estimated cost US$0.04
⠧ Thinking about prompt 3...Response received : tokens used: 10587 | Estimated cost US$0.04
```
So around US$0.36 for three summaries of each of the three papers.
## Requirements

* An OpenAI API key.
* Python3 with the packages - PyPDF2, openai, halo

## Credits

Inspired on the back of watching a youtube video by [David Shapiro](https://www.youtube.com/@DavidShapiroAutomator).  And written before I realised he had pushed his own code upto GitHub which would have saved me the effort.

## Example output
When given this Arxiv paper to summarise "[Learning to reconstruct the bubble distribution with conductivity
maps using Invertible Neural Networks and Error Diffusion](https://arxiv.org/ftp/arxiv/papers/2307/2307.02496.pdf)" and using the gpt-3.5 model (using gpt-4 would give much better results if you have access) we get the following (original paper 3,162 words, 3x different summaries 824 words):

---
# 2307.02496.pdf

## Q. Give me a very clear explanation of the core assertions, implications, and mechanics elucidated in this paper?

This paper focuses on the problem of detecting and reconstructing gas bubbles in electrolysis cells, which are used for hydrogen production. Gas bubbles can hinder the efficiency of the electrolysis process, so it is important to detect and locate them accurately. The authors propose a method that uses externally placed magnetic field sensors to measure the fluctuations caused by the gas bubbles. By solving the inverse problem of Biot-Savart's Law, they aim to estimate the conductivity in the cell, which can provide information about the bubble size and location.

To address the challenge of reconstructing high-resolution conductivity maps from limited magnetic field measurements, the authors employ Invertible Neural Networks (INNs). INNs are a type of deep neural network that can learn a bijective mapping between the conductivity map and the magnetic field measurements. This allows for the reconstruction of the conductivity map from the measurements.

The authors train the INN model using a dataset generated from a simulation of an electrolysis cell. The simulation includes a simplified model of the cell with liquid metal and non-conducting bubble voids. The magnetic field measurements are taken from sensors placed on the external walls of the cell.

The INN model consists of invertible mappings called coupling blocks, which transform the input data and produce the output conductivity map. The model is trained to minimize the reconstruction error between the ground truth conductivity map and the predicted map.

The authors evaluate the performance of the INN model using qualitative and quantitative methods. They compare the results with Tikhonov regularization, a commonly used method for solving inverse problems. The results show that the INN model outperforms Tikhonov regularization in terms of reconstruction accuracy.

Overall, this paper presents a novel approach to reconstructing the conductivity map in electrolysis cells using Invertible Neural Networks. The method shows promise in accurately detecting and locating gas bubbles, which can help improve the efficiency and safety of hydrogen production.


## Q. Can you explain the value of this in basic terms? Like you're talking to a CEO. So what? What's the bottom line here?

The bottom line is that this research aims to improve the efficiency and safety of hydrogen production through electrolysis. Electrolysis is a key process for clean energy production, but the formation of gas bubbles during the process can hinder reactions and reduce efficiency. This research focuses on using external magnetic sensors to measure the magnetic field fluctuations caused by these gas bubbles. By solving the inverse problem of Biot-Savart's Law, the researchers can estimate the conductivity inside the electrolysis cell and determine the size and location of the bubbles.

The challenge lies in reconstructing high-resolution conductivity maps from limited magnetic field measurements, which is an ill-posed problem. To overcome this, the researchers use Invertible Neural Networks (INNs) to reconstruct the conductivity field. INNs are a type of machine learning model that can capture complex relationships between input and output data. The results show that INNs outperform traditional methods like Tikhonov regularization in reconstructing the conductivity maps.

The significance of this research is that it provides a non-invasive and efficient way to detect and locate gas bubbles in electrolysis cells. By accurately estimating the bubble size and distribution, researchers and engineers can optimize the electrolysis process, improve efficiency, and reduce energy consumption. This has important implications for the development of clean energy technologies and the transition to a more sustainable future.


## Q. Can you give me an analogy or metaphor that will help explain this to a broad audience.

Sure! Imagine you have a bathtub filled with water and you want to know where the bubbles are located. However, you can't see through the bathtub, so you can't directly observe the bubbles. Instead, you decide to use a special device that measures the magnetic field around the bathtub. When bubbles are present, they cause changes in the magnetic field. By analyzing these changes, you can estimate where the bubbles are and how big they are.

To do this, you use a special type of artificial intelligence called an Invertible Neural Network (INN). The INN takes the measurements of the magnetic field and tries to reconstruct the distribution of bubbles inside the bathtub. It does this by learning the relationship between the magnetic field measurements and the bubble distribution.

However, there are some challenges. The magnetic field measurements are not very detailed, so it's difficult to accurately reconstruct the bubble distribution. Additionally, there may be measurement errors due to noise in the device. To overcome these challenges, the INN uses clever techniques to improve its performance and make better estimates of the bubble distribution.

In summary, the INN is like a detective that uses clues from the magnetic field measurements to figure out where the bubbles are hiding in the bathtub. It's a clever way to indirectly observe something that is not directly visible.
