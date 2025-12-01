"""
Gradio web interface for the RAG Chatbot.
"""
import gradio as gr
import hashlib
import time

from src.main import index_documents, answer_query
from src.utils.logger import get_logger

logger = get_logger(__name__)


def handle_indexing():
    """
    Handle document indexing button click.

    Returns:
        Status message with indexing results
    """
    try:
        logger.info("Indexing triggered from UI")
        status = index_documents()

        if status.total_documents == 0:
            return (
                "No documents found in the documents folder.\n\n"
                "Please add .txt, .md, .pdf, or .docx files to the data/documents/ "
                "folder and click 'Index Documents' again."
            )

        if status.indexed_documents == 0:
            return (
                f"Indexing failed: 0/{status.total_documents} documents indexed.\n\n"
                f"Failed: {status.failed_documents} documents\n"
                "Check logs for error details."
            )

        success_rate = (
            status.indexed_documents / status.total_documents * 100
            if status.total_documents > 0
            else 0
        )

        result_msg = (
            f"Indexing complete!\n\n"
            f"Documents indexed: {status.indexed_documents}/{status.total_documents} "
            f"({success_rate:.1f}% success)\n"
            f"Total chunks: {status.total_chunks}\n"
            f"Failed: {status.failed_documents} documents\n\n"
            f"You can now ask questions about your documents!"
        )

        if status.failed_documents > 0:
            result_msg += "\n\nSome documents failed to index. Check logs for details."

        return result_msg

    except Exception as e:
        error_msg = f"Error during indexing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


def handle_chat(message, history):
    """
    Handle chat message from user.

    Args:
        message: User's question (string or dict for Gradio 6.0)
        history: Conversation history (list of [user, assistant] pairs)

    Returns:
        Response text
    """
    try:
        # Handle both string and dict message formats
        if isinstance(message, dict):
            # Gradio 6.0 might pass message as dict with 'text' key
            query_text = message.get('text', '')
        else:
            query_text = message

        # Generate a session ID based on history length and timestamp
        # This is a simple way to have unique sessions without request object
        session_id = hashlib.md5(f"{len(history)}_{time.time()}".encode()).hexdigest()[:8]

        logger.debug(f"Processing chat message for session: {session_id}")

        # Call answer_query function with session ID
        response = answer_query(query_text=query_text, session_id=session_id)
        return response

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return "I apologize, but I encountered an error. Please try again."


def create_interface():
    """
    Create and configure the Gradio interface.

    Returns:
        Gradio Blocks app
    """
    with gr.Blocks(title="RAG Chatbot") as app:
        gr.Markdown(
            """
            # RAG-Enabled Chatbot

            Ask questions and get answers enhanced with context from your local documents.

            **How to use:**
            1. Click "Index Documents" to process files from the `data/documents/` folder
            2. Ask questions in the chat interface below
            3. Get answers based on your documents and general knowledge
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Document Management")

                index_btn = gr.Button(
                    "Index Documents",
                    variant="primary",
                    size="lg",
                )

                status_box = gr.Textbox(
                    label="Indexing Status",
                    placeholder="Click 'Index Documents' to start...",
                    lines=8,
                    interactive=False,
                )

                gr.Markdown(
                    """
                    **Supported formats:**
                    - Text files (.txt, .md)
                    - PDF documents (.pdf)
                    - Word documents (.docx)

                    **Note:** Place your documents in the `data/documents/` folder before indexing.
                    """
                )

            with gr.Column(scale=2):
                gr.Markdown("### Chat Interface")

                # Use ChatInterface with minimal parameters for Gradio 6.0 compatibility
                chatbot = gr.ChatInterface(
                    fn=handle_chat,
                    chatbot=gr.Chatbot(height=400),
                    textbox=gr.Textbox(
                        placeholder="Ask a question about your documents...",
                        container=False,
                    ),
                )

        # Wire up indexing button
        index_btn.click(fn=handle_indexing, outputs=status_box)

        gr.Markdown(
            """
            ---
            **Tips:**
            - For best results, ask specific questions about topics in your documents
            - The system retrieves the most relevant sections to answer your questions
            - If a topic isn't covered in your documents, the chatbot will use general knowledge
            """
        )

    return app


if __name__ == "__main__":
    # For testing the UI standalone
    app = create_interface()
    app.launch()
