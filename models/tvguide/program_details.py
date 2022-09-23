from __future__ import annotations

import re
import warnings
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator
from xmltv.models import (Category, EpisodeNum, Icon, Length, Rating,
                          StarRating, SubTitle, Title)

from ..xmltv import Programme


class ImageType(BaseModel):
    typeId: int
    typeName: str  # "showcard", "key art"
    providerTypeName: str


class Image(BaseModel):
    id: str
    provider: str
    imageType: ImageType
    bucketType: str
    bucketPath: str
    filename: str
    width: int
    height: int

    @property
    def url(self) -> str:
        if self.bucketType == 'local':
            return self.bucketPath
        else:
            return 'https://www.tvguide.com/a/img/catalog/' \
                    + self.bucketPath.lstrip('/')


class Genre(BaseModel):
    id: int
    name: str
    genres: List[str]


class MetacriticSummaryItem(BaseModel):
    url: Optional[str]
    score: int
    reviewCount: int


class VideoImage(BaseModel):
    imageUrl: str
    width: int
    height: int


class VideoItem(BaseModel):
    videoId: int
    providerId: int
    title: str
    slug: str
    type: str
    contentType: str
    contentTypeId: int
    videoTitle: str
    url: str
    # description: Optional[str]
    duration: int
    originalAirDate: Optional[str]
    seasonNumber: int
    episodeNumber: int
    images: List[VideoImage]


class ProgramDetails(BaseModel):
    id: int
    name: str
    parentId: Optional[int]
    description: Optional[str]
    isSportsEvent: bool
    rating: Optional[str]
    tvRating: Optional[str]
    episodeTitle: Optional[str]
    releaseYear: Optional[int]
    # seoUrl: Optional[str]
    categoryId: int
    subCategoryId: int
    episodeAirDate: Optional[str]  # /Date(timestamp + timezone offset)/
    episodeNumber: Optional[int]
    seasonNumber: Optional[int]
    mcoId: Optional[int]
    title: Optional[str]
    type: Optional[str]
    slug: Optional[str]
    typeId: Optional[int]
    images: List[Image]
    genres: List[Genre]
    duration: Optional[int]  # Seconds
    metacriticSummary: Optional[MetacriticSummaryItem]
    video: Optional[VideoItem]

    @validator('tvRating')
    def uppercase_tv_rating(cls, v):
        """Just to be sure TV rating is always uppercased."""
        if v is not None:
            v = v.upper()

        return v

    @property
    def rating_system(self):
        """Detect rating system."""
        if self.tvRating in ('12', '12A', '15', '18', 'R18', 'U'):
            return 'BBFC'

        if self.tvRating in ('TV-Y', 'TV-Y7', 'TV-G', 'TV-PG', 'TV-14', 'TV-MA'):
            return 'VCHIP'

        if self.tvRating in ('G', 'PG', 'PG-13', 'R', 'NC-17',
                             'NR', 'NO RATING', 'NOT RATED', 'UR'):
            return 'MPA'

        if self.tvRating in ('0+', '6+', '12+', '15+', '18+'):
            return 'GSRR'

        return None

    def to_xmltv(self, get_icon=None, expand_genres=True, add_tv_rating_icon=False, lang=None):
        # Add title
        program = Programme(
            title=[Title(content=[self.name], lang=lang)],
            clumpidx=None,
        )

        # Description
        if self.description:
            program.desc = self.description

        # Date
        if self.episodeAirDate:
            try:
                ts = int(re.sub(r'[^\d]', '', self.episodeAirDate)[:-3])  # tz comes always "000"
                date = datetime.fromtimestamp(ts)
                program.date = date.strftime('%Y%m%d')
            except ValueError:
                pass

        if not program.date and self.releaseYear:
            # Add trailing zeros, eg: <date>20070000</date>
            program.date = f'{self.releaseYear}0000'

        # Genres
        for genre in sorted(self.genres, key=lambda x: x.id):
            if expand_genres:
                for sub_genre in genre.genres:
                    # All subgenres are lowercased, recase it
                    sub_genre = re.sub(
                        r'[\w\s-]+&?\s?', lambda x: x.group(0).capitalize(),
                        sub_genre
                    )
                    program.category.append(
                        Category(content=[sub_genre])
                    )
            else:
                program.category.append(Category(
                    content=[genre.name]
                ))

        # Duration (without commercials)
        if self.duration:
            program.length = Length(content=[self.duration], units='seconds')

        # Subtitle
        if self.episodeTitle:
            program.sub_title.append(SubTitle(content=[self.episodeTitle]))

        # Season / Episode
        onscreen, xmltv_ns = None, None
        season, episode = self.seasonNumber, self.episodeNumber
        if season is not None and episode is not None:
            onscreen = f'S{season:02d}E{episode:02d}'

            if season > 0 and episode > 0:
                xmltv_ns = f'{season - 1}.{episode - 1}.'

        if season is not None and episode is None:
            onscreen = f'S{season:02d}E--'

            if season > 0:
                xmltv_ns = f'{season - 1}..'

        if season is None and episode is not None:
            onscreen = f'S--E{episode:02d}'

            if episode > 0:
                xmltv_ns = f'.{episode - 1}.'

        if onscreen:
            program.episode_num.append(EpisodeNum(content=[onscreen], system='onscreen'))
        if xmltv_ns:
            program.episode_num.append(EpisodeNum(content=[xmltv_ns], system='xmltv_ns'))

        # Posters
        for image in self.images:
            program.icon.append(Icon(src=image.url, width=image.width, height=image.height))

        # Rating
        if self.tvRating:
            tv_rating = Rating(value=self.tvRating)

            if self.rating_system:
                tv_rating.system = self.rating_system
            else:
                warnings.warn(f'No rating system detected for rating "{self.tvRating}"')

            # Add rating icons (some old soft could fail parsing result xml)
            if get_icon and add_tv_rating_icon:
                tv_rating_icon = get_icon(
                    icon_name=self.tvRating,
                    manifest_name='tv_rating'
                )

                if tv_rating_icon:
                    tv_rating.icon.append(tv_rating_icon)
                else:
                    warnings.warn(f'Failed to get rating icon "{self.tvRating}"')

            program.rating.append(tv_rating)

        # Star-rating
        if self.metacriticSummary and self.metacriticSummary.score > 0:
            star_rating = StarRating(
                value='%d/100' % self.metacriticSummary.score,
                system='Metascore'
            )
            if get_icon:
                metascore_icon = get_icon(
                    icon_name=str(self.metacriticSummary.score),
                    manifest_name='metascore'
                )
                if metascore_icon:
                    star_rating.icon.append(metascore_icon)
                else:
                    warnings.warn(f'Failed to get star-rating icon "{self.tvRating}"')

            program.star_rating.append(star_rating)

        return program
