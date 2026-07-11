from io import BytesIO
from tempfile import NamedTemporaryFile

import pymupdf
from anyio import Path
from pypdf import PdfReader, PdfWriter


def compress_pdf(input_path: str | Path, output_path: str | Path, dpi: int = 120, quality: int = 60) -> None:
    input_path = Path(input_path)
    output_path = Path(output_path)

    doc = pymupdf.open(str(input_path))
    try:
        doc.rewrite_images(
            dpi_threshold=dpi + 30,
            dpi_target=dpi,
            quality=quality,
        )
        doc.save(
            str(output_path),
            garbage=4,
            deflate=True,
            clean=True,
        )
    finally:
        doc.close()


async def encrypt_pdf(input_path: str | Path, output_path: str | Path, password: str) -> None:
    reader = PdfReader(str(input_path))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(user_password=password)
    buffer = BytesIO()
    writer.write(buffer)

    with Path(output_path)._path.open("wb") as file:
        file.write(buffer.getvalue())


async def compress_and_encrypt_pdf(
    input_path: str | Path,
    output_path: str | Path,
    password: str,
    dpi: int = 120,
    quality: int = 60,
) -> None:
    output_path = Path(output_path)
    output_path.parent._path.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(suffix=".pdf", dir=str(output_path.parent), delete=False) as temp_file:
        compressed_path = Path(temp_file.name)

    try:
        compress_pdf(input_path, compressed_path, dpi=dpi, quality=quality)
        await encrypt_pdf(compressed_path, output_path, password)
    finally:
        compressed_path._path.unlink(missing_ok=True)
