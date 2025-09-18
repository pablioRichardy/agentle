from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
result = md.convert("file.pdf")
result = md.convert("file.docx")
print(result.text_content)
