"""Windowed grid generator for efficient patch-based raster processing."""

from dataclasses import dataclass
from typing import Generator, Tuple


@dataclass
class RasterTileWindow:
    tile_id: int
    col_off: int
    row_off: int
    width: int
    height: int


def generate_raster_tiles(
    total_width: int,
    total_height: int,
    tile_size: int = 512,
    overlap: int = 0,
) -> Generator[RasterTileWindow, None, None]:
    """Generate non-overlapping or overlapping window offsets for memory-safe raster processing."""
    step = tile_size - overlap
    tile_id = 0

    for row in range(0, total_height, step):
        h = min(tile_size, total_height - row)
        for col in range(0, total_width, step):
            w = min(tile_size, total_width - col)
            yield RasterTileWindow(
                tile_id=tile_id,
                col_off=col,
                row_off=row,
                width=w,
                height=h,
            )
            tile_id += 1
