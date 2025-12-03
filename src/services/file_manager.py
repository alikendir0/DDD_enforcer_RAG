"""
File management service for document handling and status tracking.
"""
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import shutil

from src.models.document_file_metadata import DocumentFileMetadata
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FileManager:
    """
    Manages document files and provides metadata for UI display.

    Responsibilities:
    - List documents with metadata
    - Handle file uploads
    - Check embedding status
    - Validate file types
    - Format file information for UI
    """

    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx'}
    MAX_FILE_SIZE_MB = 50

    def __init__(self, documents_folder: str, vector_store=None):
        """
        Initialize FileManager.

        Args:
            documents_folder: Path to documents directory
            vector_store: VectorStore instance for checking embedding status
        """
        self.documents_folder = Path(documents_folder)
        self.vector_store = vector_store

        # Ensure documents folder exists
        self.documents_folder.mkdir(parents=True, exist_ok=True)

        logger.info(f"FileManager initialized with folder: {self.documents_folder}")

    def list_documents(self) -> List[DocumentFileMetadata]:
        """
        List all documents in the documents folder with metadata.

        Returns:
            List of DocumentFileMetadata objects
        """
        documents = []

        try:
            # Get all files in documents folder
            for file_path in self.documents_folder.iterdir():
                if not file_path.is_file():
                    continue

                # Skip hidden files and system files
                if file_path.name.startswith('.'):
                    continue

                # Get file extension
                file_ext = file_path.suffix.lower()

                # Create metadata
                metadata = self._create_file_metadata(file_path)
                documents.append(metadata)

            # Sort by last modified (newest first)
            documents.sort(key=lambda x: x.last_modified, reverse=True)

            logger.debug(f"Listed {len(documents)} documents from {self.documents_folder}")
            return documents

        except Exception as e:
            logger.error(f"Error listing documents: {e}", exc_info=True)
            return []

    def _create_file_metadata(self, file_path: Path) -> DocumentFileMetadata:
        """
        Create DocumentFileMetadata from a file path.

        Args:
            file_path: Path to the file

        Returns:
            DocumentFileMetadata instance
        """
        # Get file stats
        stat = file_path.stat()
        file_size_bytes = stat.st_size
        last_modified = datetime.fromtimestamp(stat.st_mtime)

        # Determine file type
        file_ext = file_path.suffix.lower()
        file_type = file_ext[1:] if file_ext else 'unknown'

        # Check if file is embedded
        is_embedded, chunk_count = self.get_embedding_status(file_path.name)

        # Determine embedding status
        if is_embedded:
            embedding_status = "✓ Embedded"
        else:
            # Check if file type is supported
            if file_ext in self.SUPPORTED_EXTENSIONS:
                embedding_status = "⏳ Pending"
            else:
                embedding_status = "❌ Unsupported"

        return DocumentFileMetadata(
            filename=file_path.name,
            file_path=file_path,
            file_type=file_type.upper(),
            file_size_bytes=file_size_bytes,
            file_size_display=self.format_file_size(file_size_bytes),
            is_embedded=is_embedded,
            embedding_status=embedding_status,
            last_modified=last_modified,
            upload_timestamp=last_modified,  # Use mtime as upload timestamp
            chunk_count=chunk_count
        )

    def get_embedding_status(self, filename: str) -> Tuple[bool, int]:
        """
        Check if a file has been embedded in the vector store.

        Args:
            filename: Name of the file to check

        Returns:
            Tuple of (is_embedded: bool, chunk_count: int)
        """
        if not self.vector_store:
            logger.warning("Vector store not available, cannot check embedding status")
            return False, 0

        try:
            # Query ChromaDB for all chunks and filter by filename
            results = self.vector_store.collection.get(
                include=['metadatas']
            )

            if not results or not results.get('metadatas'):
                return False, 0

            # Count chunks where document_path ends with this filename
            chunk_count = 0
            for metadata in results['metadatas']:
                if metadata and 'document_path' in metadata:
                    # Check if the document_path ends with this filename
                    doc_path = str(metadata['document_path'])
                    if doc_path.endswith(filename) or doc_path.endswith(filename.replace('\\', '/')):
                        chunk_count += 1

            if chunk_count > 0:
                return True, chunk_count

            return False, 0

        except Exception as e:
            logger.warning(f"Error checking embedding status for {filename}: {e}")
            return False, 0

    def handle_file_upload(self, uploaded_files) -> Tuple[bool, str, List[List[str]]]:
        """
        Handle file upload(s), validate, and save to documents folder.

        Args:
            uploaded_files: List of file paths or file objects from Gradio upload component

        Returns:
            Tuple of (success: bool, message: str, updated_file_list: List[List])
        """
        if not uploaded_files:
            return False, "No files provided", []

        # Handle single file case
        if not isinstance(uploaded_files, list):
            uploaded_files = [uploaded_files]

        success_count = 0
        errors = []

        for uploaded_file in uploaded_files:
            try:
                # Get file path
                if hasattr(uploaded_file, 'name'):
                    temp_path = Path(uploaded_file.name)
                else:
                    temp_path = Path(uploaded_file)

                filename = temp_path.name

                # Validate file type
                file_ext = temp_path.suffix.lower()
                if not self.validate_file_type(filename):
                    errors.append(f"{filename}: Unsupported file type (must be PDF, TXT, MD, or DOCX)")
                    continue

                # Get file size
                file_size = temp_path.stat().st_size
                file_size_mb = file_size / (1024 * 1024)

                # Validate file size
                if file_size_mb > self.MAX_FILE_SIZE_MB:
                    errors.append(f"{filename}: File too large ({file_size_mb:.1f} MB, max {self.MAX_FILE_SIZE_MB} MB)")
                    continue

                # Get unique destination filename
                destination = self._get_unique_filename(filename)

                # Copy file
                shutil.copy2(temp_path, destination)

                success_count += 1
                logger.info(f"File uploaded successfully: {destination.name} ({file_size_mb:.2f}MB)")

            except Exception as e:
                errors.append(f"{Path(uploaded_file).name if isinstance(uploaded_file, str) else 'file'}: {str(e)}")
                logger.error(f"Error uploading file {uploaded_file}: {e}", exc_info=True)

        # Generate result message
        if success_count > 0 and not errors:
            message = f"Successfully uploaded {success_count} file(s)"
            success = True
        elif success_count > 0 and errors:
            message = f"Uploaded {success_count} file(s) with {len(errors)} error(s): " + "; ".join(errors)
            success = True
        else:
            message = "Upload failed: " + "; ".join(errors)
            success = False

        # Get updated file list
        documents = self.list_documents()
        file_list = self.format_for_gradio_table(documents)

        return success, message, file_list

    def _get_unique_filename(self, filename: str) -> Path:
        """
        Get a unique filename by appending _1, _2, etc. if file exists.

        Args:
            filename: Original filename

        Returns:
            Path to unique filename
        """
        destination = self.documents_folder / filename

        if not destination.exists():
            return destination

        # File exists, find unique name
        stem = destination.stem
        suffix = destination.suffix
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_destination = self.documents_folder / new_name
            if not new_destination.exists():
                logger.info(f"Renamed {filename} to {new_name} to avoid conflict")
                return new_destination
            counter += 1

    def validate_file_type(self, filename: str) -> bool:
        """
        Validate if file type is supported.

        Args:
            filename: Name of the file

        Returns:
            True if file type is supported
        """
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.SUPPORTED_EXTENSIONS

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB", "234 KB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def format_for_gradio_table(self, documents: List[DocumentFileMetadata]) -> List[List[str]]:
        """
        Format document list for Gradio Dataframe display.

        Args:
            documents: List of DocumentFileMetadata objects

        Returns:
            List of rows, each row is [Filename, Type, Size, Status, Modified, Chunks]
        """
        rows = []

        for doc in documents:
            row = [
                doc.filename,
                doc.file_type.upper(),
                doc.file_size_display,
                doc.embedding_status,
                doc.last_modified.strftime("%Y-%m-%d %H:%M"),
                str(doc.chunk_count) if doc.chunk_count > 0 else "-"
            ]
            rows.append(row)

        return rows

    def delete_document(self, filename: str, delete_embeddings: bool = True) -> Tuple[bool, str]:
        """
        Delete a document from the documents folder and optionally its embeddings.

        Args:
            filename: Name of the file to delete
            delete_embeddings: If True, also delete embeddings from vector store

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            file_path = self.documents_folder / filename

            # Check if file exists
            if not file_path.exists():
                return False, f"File not found: {filename}"

            # Delete embeddings from vector store if requested
            if delete_embeddings and self.vector_store:
                try:
                    # Check if collection is initialized
                    if not hasattr(self.vector_store, 'collection') or self.vector_store.collection is None:
                        logger.warning(f"Vector store collection not initialized, skipping embedding deletion for {filename}")
                    else:
                        # Get all chunk IDs for this document
                        results = self.vector_store.collection.get(
                            include=['metadatas']
                        )

                        # Find chunk IDs that belong to this document
                        chunk_ids_to_delete = []
                        if results and results.get('ids') and results.get('metadatas'):
                            for i, metadata in enumerate(results['metadatas']):
                                if metadata and 'document_path' in metadata:
                                    doc_path = str(metadata['document_path'])
                                    # Check if document_path ends with this filename
                                    if doc_path.endswith(filename) or doc_path.endswith(filename.replace('\\', '/')):
                                        if i < len(results['ids']):
                                            chunk_ids_to_delete.append(results['ids'][i])

                        # Delete the chunks
                        if chunk_ids_to_delete:
                            self.vector_store.collection.delete(ids=chunk_ids_to_delete)
                            logger.info(f"Deleted {len(chunk_ids_to_delete)} embeddings for {filename}")
                        else:
                            logger.info(f"No embeddings found for {filename}")

                except Exception as e:
                    logger.warning(f"Error deleting embeddings for {filename}: {e}", exc_info=True)
                    # Continue with file deletion even if embedding deletion fails

            # Delete the file
            file_path.unlink()
            logger.info(f"Deleted file: {filename}")

            return True, f"Successfully deleted: {filename}"

        except Exception as e:
            error_msg = f"Error deleting {filename}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def delete_documents(self, filenames: List[str], delete_embeddings: bool = True) -> Tuple[bool, str, List[List[str]]]:
        """
        Delete multiple documents from the documents folder.

        Args:
            filenames: List of filenames to delete
            delete_embeddings: If True, also delete embeddings from vector store

        Returns:
            Tuple of (success: bool, message: str, updated_file_list: List[List])
        """
        if not filenames:
            return False, "No files selected for deletion", []

        success_count = 0
        errors = []

        for filename in filenames:
            success, message = self.delete_document(filename, delete_embeddings)
            if success:
                success_count += 1
            else:
                errors.append(message)

        # Generate result message
        if success_count > 0 and not errors:
            message = f"Successfully deleted {success_count} file(s)"
            success = True
        elif success_count > 0 and errors:
            message = f"Deleted {success_count} file(s) with {len(errors)} error(s): " + "; ".join(errors)
            success = True
        else:
            message = "Deletion failed: " + "; ".join(errors)
            success = False

        # Get updated file list
        documents = self.list_documents()
        file_list = self.format_for_gradio_table(documents)

        return success, message, file_list
