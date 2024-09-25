import logging

from litellm import completion

logger = logging.getLogger(__name__)


class AiToTssTextConverter:
    def __init__(self, model_name: str, api_key: str) -> None:
        """
        Initialize the AITextConverter with a model name and API key.

        Args:
            model_name (str): The name of the model to load.
            api_key (str): The API key for authentication.
        """
        self.model_name = model_name
        self.api_key = api_key
        self.system_prompt = """\
Convert text to a format optimized for Text-to-Speech (TTS) systems. Follow these instructions:

- Use clear language and natural speech patterns.
- Describe mathematical formulas in spoken words.
- Summarize tables, highlighting key points and trends.
- Indicate when interpreting a formula, table, or non-textual element.
- Omit commented text (between /* */ or after //).
- Omit or briefly describe non-verbal elements (e.g., LaTeX commands, HTML tags, code comments, markup syntax). Describe them concisely if they would contribute to understanding when read aloud.
- Replace URL links with "link" or a brief description if relevant.
- Spell out acronyms and abbreviations on first use.
- Use punctuation to guide pauses and intonation.
- When a document has a title, use this as the starting output.
- Stay as close as possible to the original text while adhering to the guidelines.

Enclose the converted text between <TTS_START> and <TTS_END> tags.
"""
        self.conversion_prompt = """\
```
{text}
```

Convert the above text for Text-to-Speech (TTS) systems. Follow these steps:
- Apply all instructions from the system prompt.
- Ensure clarity and ease of understanding when read aloud.
- Begin the converted text with <TTS_START> and end with <TTS_END>.
- Produce only the converted text without additional commentary.

Proceed with the conversion now.
"""

        logger.info(f"Initialized AITextConverter with model {self.model_name}")

    def final_parsing(self, raw_response: str) -> str:
        """
        Look for the <TTS_START> and <TTS_END> tags in the raw response and return the enclosed text.
        If the <TTS_START> tag is missing, raise a ValueError.
        If the <TTS_END> tag is missing, raise a ValueError. #TODO: instead of an error reprompt the LLM to keep going
        """

        start_tag = "<TTS_START>"
        end_tag = "<TTS_END>"

        start_index = raw_response.find(start_tag)
        end_index = raw_response.find(end_tag)

        if start_index == -1:
            raise ValueError("The <TTS_START> tag is missing in the response.")
        if end_index == -1:
            raise ValueError("The <TTS_END> tag is missing in the response.")

        # Extract the text between the tags
        return raw_response[start_index + len(start_tag) : end_index].strip()

    def convert_text(self, input_text: str) -> str:
        """
        Convert the input text using the defined prompts and the loaded model.

        Args:
            input_text (str): The text to be converted.

        Yields:
            str: Intermediate converted text suitable for TTS.
        """

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.conversion_prompt.format(text=input_text)},
        ]

        response = completion(model=self.model_name, messages=messages, stream=True, api_key=self.api_key)

        final_output = ""
        for part in response:
            content = part.choices[0].delta.content or ""
            final_output += content
            yield content  # Yield intermediate content

        # Perform final processing on the complete response
        processed_output = self.final_parsing(final_output)
        logger.info(f"Final processed output:\n {processed_output}")
        yield processed_output  # Yield the final processed output


if __name__ == "__main__":
    import os

    import dotenv

    dotenv.load_dotenv()

    model_name = "gpt-4o-mini"  # Replace with your desired model name"

    api_key = os.getenv("OPENAI_API_KEY")

    ai_converter = AiToTssTextConverter(model_name, api_key)

    test_text = """We aim to have the normalized loss value of the untrained model
at 1 and the trained model at 0. We calculated the normalization with
the following formula:
𝐿𝑛𝑜𝑟 𝑚𝑎𝑙𝑖𝑧𝑒𝑑 = 𝛼 𝐿𝑢𝑛𝑛𝑜𝑟 𝑚𝑎𝑙𝑖𝑧𝑒𝑑 ¸ 𝛽 (3)
With:
𝛼 = 𝑦2  𝑦1
𝑥2  𝑥1
(4)
𝛽 = 𝑦1  𝑎 𝑥1 (5)
Where 𝑦1 is the target loss value for the untrained model (in our case
𝑦1 = 1), 𝑦2 is the target loss value for the trained model (in our case
𝑦2 = 0), 𝑥1 is the measured loss of the untrained model and 𝑥2 is the
measured loss of the trained model. We can now combine different
loss functions by adding the normalized loss functions together since
the loss functions are now on the same scale"""

    # converted_text = ai_converter.convert_text(test_text)
    # print(converted_text)

    # Variable to store the final processed output
    previous_output = ""

    # Iterate over the generator to print intermediate and final outputs
    for output in ai_converter.convert_text(test_text):
        # Print the previous intermediate output on the same line
        print(previous_output, end="", flush=True)
        previous_output = output  # Update previous_output with the latest output

    final_output = previous_output

    # Print a newline after the final output
    print("")

    # Use the final_output variable as needed
    print("--------------- Final processed output ----------")
    print(final_output)
