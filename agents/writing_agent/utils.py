def write_markdown_file(content, filename):
  """Writes the given content as a markdown file to the local directory.

  Args:
    content: The string content to write to the file.
    filename: The filename to save the file as.
  """
  with open(f"{filename}.md", "w") as f:
    f.write(content)

def count_words(text):
        """
        Count the number of words in the given text.
        
        Args:
            text (str): The input text to count words from.
        
        Returns:
            int: The number of words in the text.
        """
        # Split the text into words and count them
        words = text.split()
        return len(words)