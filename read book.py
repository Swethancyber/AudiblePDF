import pyttsx3
import PyPDF2

def read_pdf(file_path):
    try:
        # Initialize the text-to-speech engine
        engine = pyttsx3.init()

        # Open the PDF file
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Extract text from each page
            for page in reader.pages:
                text += page.extract_text() + "\n"  # Add a newline for better readability

        # Speak the content
        engine.say(text)
        engine.runAndWait()
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Specify the path to your PDF file
    book_path = 'C:/Users/username.pdf(Enter the path of the pdf file)'  # For Windows
    read_pdf(book_path)
