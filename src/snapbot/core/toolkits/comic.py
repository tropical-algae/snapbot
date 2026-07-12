from dataclasses import dataclass
from typing import Literal

from anyio import Path
from jmcomic import Feature, JmMagicConstants, JmOption, create_option_by_file, download_photo_async

from snapbot.common.configs import settings

JmTime = Literal["a", "t", "w", "m"]
JmCategory = Literal[
    "0",
    "doujin",
    "single",
    "short",
    "another",
    "hanman",
    "meiman",
    "doujin_cosplay",
    "3D",
    "english_site",
]
JmOrderBy = Literal["mr", "mv", "mp", "tf", "md", "tr"]


@dataclass(frozen=True)
class JmAlbumItem:
    album_id: str
    title: str


class JmComicToolkit:
    def __init__(self, option_file: str = settings.toolkits.jm_option_file) -> None:
        self.option_file = Path(option_file)
        self.option: JmOption | None = None

    async def get_option(self) -> JmOption:
        if self.option is not None:
            return self.option

        try:
            self.option = create_option_by_file(str(self.option_file))
        except OSError:
            self.option = JmOption.default()
        return self.option

    async def new_runtime_option(self) -> JmOption:
        option = (await self.get_option()).copy_option()
        option.client.src_dict["impl"] = "api"
        option.client.src_dict["async_impl"] = "async_api"
        option.plugins.src_dict.clear()
        return option

    @staticmethod
    def parse_album_items(page: object) -> list[JmAlbumItem]:
        iter_id_title = getattr(page, "iter_id_title", None)
        items = iter_id_title() if callable(iter_id_title) else page
        return [JmAlbumItem(album_id=str(album_id), title=str(title)) for album_id, title in items]

    async def search_albums(self, keyword: str) -> list[JmAlbumItem]:
        option = await self.new_runtime_option()
        async with option.new_jm_async_client() as client:
            page = await client.search_site(search_query=keyword, page=1)
        return self.parse_album_items(page)

    async def ranking(
        self, time: JmTime, category: JmCategory, order_by: JmOrderBy, max_count: int
    ) -> list[JmAlbumItem]:
        option = await self.new_runtime_option()
        async with option.new_jm_async_client() as client:
            page = await client.categories_filter(
                page=1,
                time=time,
                category=category,
                order_by=order_by,
            )
        return self.parse_album_items(page)[:max_count]

    async def download_album_pdf(
        self,
        album_id: str,
        pdf_dir: str | Path,
        image_dir: str | Path,
        filename: str,
    ) -> Path:
        pdf_dir = Path(pdf_dir)
        image_dir = Path(image_dir)
        await pdf_dir.mkdir(parents=True, exist_ok=True)
        await image_dir.mkdir(parents=True, exist_ok=True)

        option = await self.new_runtime_option()
        option.dir_rule.base_dir = str(image_dir)

        await download_photo_async(
            album_id,
            option=option,
            extra=Feature.export_pdf(
                pdf_dir=str(pdf_dir),
                filename_rule=filename,
                delete_original_file=True,
            ),
        )

        expected_pdf = pdf_dir / f"{filename}.pdf"
        if await expected_pdf.exists():
            return expected_pdf

        latest_pdf: Path | None = None
        latest_mtime = -1.0
        async for filepath in pdf_dir.glob(f"{filename}*.pdf"):
            stat = filepath.stat()
            if stat.st_mtime > latest_mtime:
                latest_pdf = Path(filepath)
                latest_mtime = stat.st_mtime

        if latest_pdf is None:
            raise FileNotFoundError(f"JM album {album_id} was downloaded but no PDF was generated.")
        return latest_pdf


jm_comic_toolkit = JmComicToolkit()

JM_TIME_VALUES = {
    "all": JmMagicConstants.TIME_ALL,
    "today": JmMagicConstants.TIME_TODAY,
    "week": JmMagicConstants.TIME_WEEK,
    "month": JmMagicConstants.TIME_MONTH,
}
JM_CATEGORY_VALUES = {
    "all": JmMagicConstants.CATEGORY_ALL,
    "doujin": JmMagicConstants.CATEGORY_DOUJIN,
    "single": JmMagicConstants.CATEGORY_SINGLE,
    "short": JmMagicConstants.CATEGORY_SHORT,
    "another": JmMagicConstants.CATEGORY_ANOTHER,
    "hanman": JmMagicConstants.CATEGORY_HANMAN,
    "meiman": JmMagicConstants.CATEGORY_MEIMAN,
    "doujin_cosplay": JmMagicConstants.CATEGORY_DOUJIN_COSPLAY,
    "3d": JmMagicConstants.CATEGORY_3D,
    "english_site": JmMagicConstants.CATEGORY_ENGLISH_SITE,
}
JM_ORDER_BY_VALUES = {
    "latest": JmMagicConstants.ORDER_BY_LATEST,
    "view": JmMagicConstants.ORDER_BY_VIEW,
    "picture": JmMagicConstants.ORDER_BY_PICTURE,
    "like": JmMagicConstants.ORDER_BY_LIKE,
    "comment": JmMagicConstants.ORDER_BY_COMMENT,
    "score": JmMagicConstants.ORDER_BY_SCORE,
}
