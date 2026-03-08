from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QBuffer, QIODevice

def take_screenshot(image_format: str = "PNG", quality: int = -1) -> bytes:
    """
    Captures the user's primary screen and returns the image data as bytes.
    
    Args:
        image_format (str): The image format to save as (e.g., "PNG", "JPEG").
                            PNG is lossless but larger; JPEG is smaller but lossy.
        quality (int): The image quality factor (0-100). -1 uses the default 
    settings for the chosen format.
    Returns:
        bytes: The encoded image data ready to be sent to an API.
        
    Raises:
        RuntimeError: If a QApplication instance is not currently running.
    """
    #  Ensure the Qt Application is actually running
    app = QApplication.instance()
    if not app:
        raise RuntimeError("Cannot take screenshot: QApplication instance is missing.")
        
    # Get the primary screen
    screen = app.primaryScreen()
    if not screen:
        raise RuntimeError("Cannot take screenshot: No primary screen detected.")
        
    #  Capture the screen (0 represents the entire window/desktop area)
    screenshot = screen.grabWindow(0)
    
    # Convert the QPixmap to a byte array
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    
    # Save the screenshot into the buffer with the specified format and quality
    success = screenshot.save(buffer, image_format, quality)
    if not success:
        raise ValueError(f"Failed to save screenshot in '{image_format}' format.")
        
    return buffer.data().data()