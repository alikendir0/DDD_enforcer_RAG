"""
Gradio web interface for the RAG Chatbot with advanced statistics and configuration.
"""
import gradio as gr
import hashlib
import time

from src.main import index_documents, answer_query
import src.main
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


def format_context_html(context_metadata):
    """
    Format retrieval context as collapsible HTML using <details> tag.

    Args:
        context_metadata: List of dicts with chunk_text, score, document_name, chunk_index

    Returns:
        HTML string with formatted context
    """
    if not context_metadata:
        return ""

    html_parts = ["\n\n---\n\n**Retrieved Context:**\n\n"]

    for i, ctx in enumerate(context_metadata, 1):
        score = ctx['score']
        doc_name = ctx['document_name']
        chunk_idx = ctx.get('chunk_index', '?')
        chunk_text = ctx['chunk_text']

        # Create collapsible section for each chunk
        html_parts.append(
            f"<details>\n"
            f"<summary><b>Chunk {i}</b> from <code>{doc_name}</code> "
            f"(chunk #{chunk_idx}, similarity: {score:.3f})</summary>\n\n"
            f"{chunk_text}\n\n"
            f"</details>\n\n"
        )

    return "".join(html_parts)


def handle_chat(message, history, session_state):
    """
    Handle chat message from user.

    Args:
        message: User's question (string or dict for Gradio 6.0)
        history: Conversation history (list of [user, assistant] pairs)
        session_state: Session ID state

    Returns:
        Response text with optional context
    """
    try:
        # Handle both string and dict message formats
        if isinstance(message, dict):
            # Gradio 6.0 might pass message as dict with 'text' key
            query_text = message.get('text', '')
        else:
            query_text = message

        # Use session ID from state
        session_id = session_state

        logger.debug(f"Processing chat message for session: {session_id}")

        # Check if context display is enabled
        show_context = False
        if src.main.config_manager:
            config = src.main.config_manager.get_current_config()
            show_context = config.show_context_enabled

        # Call answer_query function with session ID
        if show_context:
            response, context_metadata = answer_query(
                query_text=query_text,
                session_id=session_id,
                return_context=True
            )
            # Append formatted context to response
            if context_metadata:
                context_html = format_context_html(context_metadata)
                response = response + context_html
        else:
            response = answer_query(query_text=query_text, session_id=session_id)

        return response

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return "I apologize, but I encountered an error. Please try again."


def update_statistics(session_id):
    """
    Update and format statistics display.

    Args:
        session_id: Session identifier

    Returns:
        Formatted statistics dict for JSON display
    """
    try:
        if not src.main.stats_tracker:
            return {"status": "Stats tracker not initialized"}

        stats = src.main.stats_tracker.format_stats_for_display(session_id)
        return stats

    except Exception as e:
        logger.error(f"Error updating statistics: {e}", exc_info=True)
        return {"error": str(e)}


def save_configuration(top_k, chunk_size, chunk_overlap, show_context):
    """
    Save configuration changes.

    Args:
        top_k: Number of chunks to retrieve
        chunk_size: Token count per chunk
        chunk_overlap: Overlapping tokens between chunks
        show_context: Whether to show context by default

    Returns:
        Status message
    """
    try:
        # Ensure services are initialized
        if not src.main.config_manager:
            src.main.initialize_services()
        
        if not src.main.config_manager:
            return "Configuration manager not initialized"

        # Check if re-indexing required
        reindex_needed = src.main.config_manager.detect_reindex_required(chunk_size, chunk_overlap)

        # Save configuration
        success, message = src.main.config_manager.save_config(
            top_k=top_k,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            show_context_enabled=show_context
        )

        if success:
            if reindex_needed:
                return (
                    f"{message}\n\n"
                    "⚠️ Warning: Chunk size or overlap changed. "
                    "Please re-index your documents for changes to take effect."
                )
            return f"✅ {message}"
        else:
            return f"❌ {message}"

    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


def reset_configuration():
    """
    Reset configuration to default values.

    Returns:
        Tuple of (status_message, top_k, chunk_size, chunk_overlap, show_context)
    """
    try:
        # Ensure services are initialized
        if not src.main.config_manager:
            src.main.initialize_services()
        
        if not src.main.config_manager:
            return "Configuration manager not initialized", 3, 512, 0, False

        success, config = src.main.config_manager.reset_to_defaults()

        if success:
            return (
                "✅ Configuration reset to defaults",
                config.top_k,
                config.chunk_size,
                config.chunk_overlap,
                config.show_context_enabled
            )
        else:
            return (
                "❌ Failed to reset configuration",
                config.top_k,
                config.chunk_size,
                config.chunk_overlap,
                config.show_context_enabled
            )

    except Exception as e:
        logger.error(f"Error resetting configuration: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", 3, 512, 0, False


def initialize_session():
    """
    Load current configuration values on app start.

    Returns:
        Tuple of (top_k, chunk_size, chunk_overlap, show_context)
    """
    try:
        # Ensure services are initialized
        if not src.main.config_manager:
            src.main.initialize_services()
        
        if not src.main.config_manager:
            return 3, 512, 0, False

        config = src.main.config_manager.get_current_config()
        return config.top_k, config.chunk_size, config.chunk_overlap, config.show_context_enabled

    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        return 3, 512, 0, False


def load_file_list():
    """
    Load and format the file list for display.

    Returns:
        List of rows for Gradio Dataframe
    """
    try:
        if not src.main.file_manager:
            return []

        documents = src.main.file_manager.list_documents()
        rows = src.main.file_manager.format_for_gradio_table(documents)

        logger.debug(f"Loaded {len(rows)} files for display")
        return rows

    except Exception as e:
        logger.error(f"Error loading file list: {e}", exc_info=True)
        return []


def on_file_upload(files):
    """
    Handle file upload from Gradio component.

    Args:
        files: Single file path or list of file paths from Gradio

    Returns:
        Tuple of (upload_status_message, updated_file_list)
    """
    try:
        if not src.main.file_manager:
            return "File manager not initialized", load_file_list()

        if not files:
            return "No files selected", load_file_list()

        # Handle file upload using new FileManager signature
        success, message, updated_list = src.main.file_manager.handle_file_upload(files)

        # Format message with emoji
        if success:
            status_msg = f"✅ {message}"
        else:
            status_msg = f"❌ {message}"

        logger.info(f"File upload completed: {message}")

        return status_msg, updated_list

    except Exception as e:
        error_msg = f"Error handling file upload: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg, load_file_list()


def trigger_indexing():
    """
    Trigger document indexing with current configuration.

    Returns:
        Status message from indexing operation
    """
    try:
        if not src.main.config_manager:
            return "Configuration manager not initialized"

        # Get current configuration
        config = src.main.config_manager.get_current_config()

        logger.info("Starting indexing from UI with config: " +
                   f"chunk_size={config.chunk_size}, chunk_overlap={config.chunk_overlap}")

        # Call index_documents with configuration
        status = index_documents(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )

        # Format result message (same as handle_indexing)
        if status.total_documents == 0:
            return (
                "No documents found in the documents folder.\n\n"
                "Please upload files using the File Management section above."
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


def create_interface():
    """
    Create and configure the Gradio interface with tabs and statistics.

    Returns:
        Gradio Blocks app
    """
    with gr.Blocks(title="RAG Chatbot") as app:
        gr.Markdown(
            """
            # RAG-Enabled Chatbot with Advanced Analytics

            Ask questions and get answers enhanced with context from your local documents.
            Monitor usage, configure parameters, and manage files through the interface.
            """
        )

        # Hidden state for session ID (generated once per page load)
        session_id_state = gr.State(value=hashlib.md5(
            f"{time.time()}".encode()
        ).hexdigest()[:16])

        # Main tabs
        with gr.Tabs() as main_tabs:
            # Tab 1: Chat
            with gr.Tab("Chat", id="chat_tab"):
                gr.Markdown("### Ask Questions About Your Documents")

                # Chat interface
                with gr.Row():
                    with gr.Column(scale=2):
                        chatbot_component = gr.Chatbot(
                            height=500,
                            label="Conversation"
                        )
                        msg_input = gr.Textbox(
                            placeholder="Ask a question about your documents...",
                            label="Your Question",
                            lines=2
                        )
                        with gr.Row():
                            submit_btn = gr.Button("Submit", variant="primary")
                            clear_btn = gr.Button("Clear Chat")

                        # Example queries section
                        with gr.Accordion("💡 Example Questions", open=True):
                            gr.Markdown(
                                """
                                Try these example queries based on the sample documents:

                                **Python Programming:**
                                - "What are the basic data types in Python?"
                                - "How do I handle errors in Python?"
                                - "What are the best practices for Python development?"

                                **Machine Learning:**
                                - "What is the difference between supervised and unsupervised learning?"
                                - "How do I prevent overfitting in machine learning models?"
                                - "What metrics should I use for classification problems?"

                                **Data Science:**
                                - "What is the data science workflow?"
                                - "How should I handle missing values in my dataset?"
                                - "What tools are commonly used in data science?"

                                💡 *Tip: Click "Index Documents" in the File Management tab first to enable these questions!*
                                """
                            )

                    with gr.Column(scale=1):
                        # Statistics accordion in chat tab
                        with gr.Accordion("Statistics", open=False) as stats_accordion:
                            gr.Markdown("Real-time usage statistics for this session")
                            stats_json = gr.JSON(label="Session Stats", value={})
                            refresh_stats_btn = gr.Button("Refresh Stats", size="sm")

            # Tab 2: File Management
            with gr.Tab("File Management", id="file_tab"):
                gr.Markdown("### Manage Documents and Configuration")

                # Configuration accordion
                with gr.Accordion("Configuration", open=True):
                    gr.Markdown("**RAG Parameters** - Adjust retrieval and chunking settings")

                    top_k_slider = gr.Slider(
                        minimum=1,
                        maximum=10,
                        step=1,
                        value=3,
                        label="Top-K",
                        info="Number of chunks to retrieve per query (1-10)"
                    )

                    chunk_size_slider = gr.Slider(
                        minimum=256,
                        maximum=1024,
                        step=64,
                        value=512,
                        label="Chunk Size",
                        info="Token count per document chunk (256-1024)"
                    )

                    chunk_overlap_slider = gr.Slider(
                        minimum=0,
                        maximum=256,
                        step=16,
                        value=0,
                        label="Chunk Overlap",
                        info="Overlapping tokens between chunks (0-256)"
                    )

                    show_context_checkbox = gr.Checkbox(
                        label="Show retrieval context by default",
                        value=False,
                        info="Display document chunks used to generate responses"
                    )

                    with gr.Row():
                        save_config_btn = gr.Button("Save Configuration", variant="primary")
                        reset_config_btn = gr.Button("Reset to Defaults")

                    config_status = gr.Textbox(
                        label="Configuration Status",
                        placeholder="Adjust parameters and click 'Save Configuration'",
                        lines=2,
                        interactive=False
                    )

                gr.Markdown("---")

                # File upload section
                gr.Markdown("### File Management")
                gr.Markdown("Upload documents or manage existing files in your corpus.")

                with gr.Row():
                    file_upload = gr.File(
                        label="Upload Documents",
                        file_count="multiple",
                        file_types=[".pdf", ".txt", ".md", ".docx"],
                        type="filepath"
                    )

                upload_status = gr.Textbox(
                    label="Upload Status",
                    placeholder="Select files to upload...",
                    lines=2,
                    interactive=False
                )

                # File list table
                gr.Markdown("### Document Library")

                file_list_table = gr.Dataframe(
                    headers=["Filename", "Type", "Size", "Status", "Modified", "Chunks"],
                    datatype=["str", "str", "str", "str", "str", "str"],
                    label="Documents",
                    interactive=False,
                    wrap=True
                )

                refresh_files_btn = gr.Button("Refresh File List", size="sm")

                gr.Markdown("---")

                gr.Markdown(
                    """
                    **Document Indexing:**
                    Click "Index Documents" to process all files in your document library.

                    **Supported formats:** .txt, .md, .pdf, .docx
                    """
                )

                index_btn = gr.Button(
                    "Index Documents",
                    variant="primary",
                    size="lg",
                )

                status_box = gr.Textbox(
                    label="Indexing Status",
                    placeholder="Click 'Index Documents' to start...",
                    lines=6,
                    interactive=False,
                )

            # Tab 3: Statistics (detailed view)
            with gr.Tab("Statistics", id="stats_tab"):
                gr.Markdown("### Detailed Usage Statistics")

                gr.Markdown(
                    """
                    Monitor token usage, costs, and database metrics for your current session.
                    Statistics reset when you refresh the page.
                    """
                )

                detailed_stats_json = gr.JSON(label="Session Statistics", value={})
                refresh_detailed_stats_btn = gr.Button("Refresh Statistics", variant="primary")

        # Event handlers

        # Chat submission
        def submit_message(message, history, session_id):
            """Handle message submission and update statistics."""
            response = handle_chat(message, history, session_id)
            # Update history with proper message format
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ]
            # Get updated stats
            stats = update_statistics(session_id)
            return history, "", stats, stats

        submit_btn.click(
            fn=submit_message,
            inputs=[msg_input, chatbot_component, session_id_state],
            outputs=[chatbot_component, msg_input, stats_json, detailed_stats_json]
        )

        msg_input.submit(
            fn=submit_message,
            inputs=[msg_input, chatbot_component, session_id_state],
            outputs=[chatbot_component, msg_input, stats_json, detailed_stats_json]
        )

        # Clear chat
        clear_btn.click(
            fn=lambda: ([], {}),
            outputs=[chatbot_component, stats_json]
        )

        # Refresh statistics buttons
        refresh_stats_btn.click(
            fn=update_statistics,
            inputs=[session_id_state],
            outputs=[stats_json]
        )

        refresh_detailed_stats_btn.click(
            fn=update_statistics,
            inputs=[session_id_state],
            outputs=[detailed_stats_json]
        )

        # Indexing button - now using trigger_indexing with config
        index_btn.click(fn=trigger_indexing, outputs=status_box)

        # Configuration buttons
        save_config_btn.click(
            fn=save_configuration,
            inputs=[top_k_slider, chunk_size_slider, chunk_overlap_slider, show_context_checkbox],
            outputs=[config_status]
        )

        reset_config_btn.click(
            fn=reset_configuration,
            outputs=[config_status, top_k_slider, chunk_size_slider, chunk_overlap_slider, show_context_checkbox]
        )

        # File management event handlers
        file_upload.change(
            fn=on_file_upload,
            inputs=[file_upload],
            outputs=[upload_status, file_list_table]
        )

        refresh_files_btn.click(
            fn=load_file_list,
            outputs=[file_list_table]
        )

        # Load file list when switching to File Management tab
        def load_file_management_data(tab_id):
            if tab_id == "file_tab":
                return load_file_list()
            return None

        main_tabs.select(
            fn=load_file_management_data,
            inputs=[main_tabs],
            outputs=[file_list_table]
        )

        # Initialize configuration on load
        app.load(
            fn=initialize_session,
            outputs=[top_k_slider, chunk_size_slider, chunk_overlap_slider, show_context_checkbox]
        )

        gr.Markdown(
            """
            ---
            **Tips:**
            - For best results, ask specific questions about topics in your documents
            - The system retrieves the most relevant sections to answer your questions
            - Monitor your token usage and costs in real-time through the Statistics tab
            """
        )

    return app


if __name__ == "__main__":
    # For testing the UI standalone
    app = create_interface()
    app.launch()
