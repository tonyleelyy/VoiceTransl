import openai
import json
import os

def summarize(input_file, address, model, token, prompt):
    """
    Query OpenAI to generate a summary with timestamps (mm:ss format) from the input file
    and save it to input_file.summary.txt.
    
    Args:
        input_file: Path to the file containing content to summarize
        address: API endpoint or service address
        model: OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
        token: OpenAI API key
    
    Returns:
        str: Generated summary with timestamps
    """
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=token, base_url=address)
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create prompt for summarization with timestamps in Chinese
    prompt = f"""请为以下内容创建一个带有时间戳（mm:ss格式）的粗略摘要，不多于10个事件。
    请关注关键事件和重要时刻，并确保所有时间戳都采用分钟:秒钟格式。
    
    {content}""" if not prompt else f"""{prompt}

    {content}"""
    
    # Query OpenAI API
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        # Extract the summary
        summary = response.choices[0].message.content
        
        # Create output filename
        output_file = f"{input_file}.summary.txt"
        
        # Save summary to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"Summary saved to {output_file}")
        except Exception as e:
            print(f"Error saving summary to file: {e}")
        
        return summary
        
    except Exception as e:
        print(f"Error querying OpenAI API: {e}")
        return None