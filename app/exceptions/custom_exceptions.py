# document_processor/app/exceptions/custom_exceptions.py
class DocumentProcessingError(Exception):
    """Base exception for document processing errors"""
    pass

class UnsupportedFileTypeError(DocumentProcessingError):
    """Raised when an unsupported file type is provided"""
    pass

class ConversionError(DocumentProcessingError):
    """Raised when document conversion fails"""
    pass

class WebhookNotificationError(DocumentProcessingError):
    """Raised when webhook notification fails"""
    pass