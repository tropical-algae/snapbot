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

    async with await Path(output_path).open("wb") as file:
        await file.write(buffer.getvalue())


async def compress_and_encrypt_pdf(
    input_path: Path,
    output_path: Path,
    password: str | None,
    dpi: int | None,
    quality: int | None,
) -> None:
    output_path = Path(output_path)
    await output_path.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(suffix=".pdf", dir=str(output_path.parent), delete=False) as temp_file:
        compressed_path = Path(temp_file.name)

    try:
        if dpi is not None and quality is not None:
            compress_pdf(input_path, compressed_path, dpi=dpi, quality=quality)
        else:
            await input_path.replace(compressed_path)
        if password:
            await encrypt_pdf(compressed_path, output_path, password)
        else:
            await compressed_path.replace(output_path)
    finally:
        await compressed_path.unlink(missing_ok=True)
