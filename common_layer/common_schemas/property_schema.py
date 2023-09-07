from pydantic import BaseModel, validator
from typing import Any, Optional
import time
from enum import Enum

"""
Listing Type:
Sell, Rent , Others

Listed By:
Broker, Owner

Possession Type:
Ready to Move, under Construction

Category:

- Residential - Commercial - Farm
    1. House 1. Shops 1. Farm lands
    2. Flats 2. Offices 2. Farm houses
    3. Plots 3. Others

Residential Fields:

1. Type = (Apartment. Builder Floors, Farm House, Villa)
2. Bedrooms
3. Bathrooms
4. Furnishing = ( Furnishing, Semi-Furnished, Unfurnished)
5. Construction Status = (New Launch, Under Construction, Ready to Move)
6. Built up area
7. Carpet area
8. Maintenance
9. Floor no
10. Car Parking
11. Facing = ( North, East, West, South, North-East, North-West, South-East, South-West)
12. Balcony

Farm Fields:
1. Plot Area
2. Length
3. Breadth
4. Facing = ( North, East, West, South, North-East, North-West, South-East, South-West)

Commercial Fields:

1. Furnishing = ( Furnishing, Semi-Furnished, Unfurnished)
2. Construction Status = (New Launch, Under Construction, Ready to Move)
3. Built up area
4. Carpet area
5. Maintenance
6. Car Parking
7. Washrooms

Schemas:

1. Listing Type
2. Listed By
3. Possession Type
4. Category
5. Project Name
6. Description
7. Ad Title
8. Price
9. View Count
10. Video URL
11. Images
12. address
13. Region
14. recommended
15. verified
16. posted by
17. created on
18. updated on
19. property_details_id
20. candle_data_id
21. location
22. Region

Residential Property Request Schema:
    property_type: str
    bedrooms: int
    bathrooms: int
    furnishing: str
    construction_status: str
    built_up_area: float
    carpet_area: float
    maintenance: float
    floor_no: int
    car_parking: int
    facing: str
    balcony: bool
    possession_type: str
    category: str
    description: str
    project_title: str
    price: float
    video_url: str
    images: list
    address: str
    location: dict
    region_id: str
    roi_percentage: float

"""


class LocationSchema(BaseModel):
    latitude: float
    longitude: float

    @validator("latitude")
    def validate_latitude(cls, value):
        if not (-90 <= value <= 90):
            raise ValueError("Invalid Latitude Value, Must be between -90 and 90")
        return value

    @validator("longitude")
    def validate_longitude(cls, value):
        if not (-180 <= value <= 180):
            raise ValueError("Invalid Longitude Value, Must be between -180 and 180")
        return value


class ListingType(str, Enum):
    SELL = "sell"
    RENT = "rent"
    LEASE = "lease"


class ListedBy(str, Enum):
    BROKER = "broker"
    OWNER = "owner"


class PossessionType(str, Enum):
    READY_TO_MOVE = "ready_to_move"
    UNDER_CONSTRUCTION = "under_construction"
    NEW_LAUNCH = "new_launch"


class Category(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    FARM = "farm"


class ResidentialType(str, Enum):
    APARTMENT = "apartment"
    FLAT = "flat"
    FARM_HOUSE = "farm_house"
    HOUSES_AND_VILLA = "houses_and_villa"

class CommercialType(str, Enum):
    SHOPS = "shops"
    OFFICES = "offices"
    OTHERS = "others"

class FarmType(str, Enum):
    FARM_LANDS = "farm_lands"
    FARM_HOUSES = "farm_houses"


class Furnishing(str, Enum):
    FURNISHED = "furnished"
    SEMI_FURNISHED = "semi_furnished"
    UNFURNISHED = "unfurnished"


class Facing(str, Enum):
    NORTH = "north"
    EAST = "east"
    WEST = "west"
    SOUTH = "south"
    NORTH_EAST = "north_east"
    NORTH_WEST = "north_west"
    SOUTH_EAST = "south_east"
    SOUTH_WEST = "south_west"


class PropertySubCategory(str, Enum):
    RESIDENTIAL_HOUSE = "residential_house"
    RESIDENTIAL_FLATS = "residential_flats"
    RESIDENTIAL_PLOTS = "residential_plots"
    COMMERCIAL_SHOPS = "commercial_shops"
    COMMERCIAL_OFFICES = "commercial_offices"
    COMMERCIAL_OTHERS = "commercial_others"
    FARM_LANDS = "farm_lands"
    FARM_HOUSES = "farm_houses"


class CustomBaseSchema(BaseModel):
    created_at: float = time.time()
    updated_at: float = time.time()


class PropertySchema(CustomBaseSchema):
    listing_type: str
    listed_by: str
    listed_by_user_id: str
    is_investment_property: bool = False
    possession_type: str
    category: str
    description: str
    project_logo: str
    project_title: str
    price: float
    area: float
    view_count: int
    video_url: str
    images: Optional[list] = []
    address: str
    location: dict
    region_id: str
    verified: bool
    property_details_id: str
    candle_data_id: str
    roi_percentage: float
    project_brochure: Optional[str] = ""
    project_document: Optional[str] = ""
    document_title: Optional[str] = ""
    brochure_title: Optional[str] = ""


    @validator("listing_type")
    def validate_listing_type(cls, value):
        if value not in [listing_type.value for listing_type in ListingType]:
            raise ValueError("Invalid Listing Type. Must be one of sell, rent, lease")
        return value

    @validator("listed_by")
    def validate_listed_by(cls, value):
        if value not in [listed_by.value for listed_by in ListedBy]:
            raise ValueError("Invalid Listed By. Must be one of broker, owner")
        return value

    @validator("possession_type")
    def validate_possession_type(cls, value):
        if value not in [possession_type.value for possession_type in PossessionType]:
            raise ValueError(
                "Invalid Possession Type. Must be one of ready_to_move, under_construction, others"
            )
        return value

    @validator("category")
    def validate_category(cls, value):
        if value not in [category.value for category in Category]:
            raise ValueError(
                "Invalid Category. Must be one of residential, commercial, farm"
            )
        return value


class ResidentialPropertyRequestSchema(CustomBaseSchema):
    is_investment_property: bool = False
    region_id: str
    listing_type: str
    listed_by: str
    property_type: str
    bedrooms: int
    bathrooms: int
    furnishing: str
    built_up_area: float
    carpet_area: float
    maintenance: float
    floor_no: int
    car_parking: int
    facing: str
    balcony: bool
    possession_type: str
    description: str
    project_title: str
    price: float
    video_url: str
    address: str
    location: LocationSchema
    roi_percentage: float

    @validator("listing_type")
    def validate_listing_type(cls, value):
        if value not in [listing_type.value for listing_type in ListingType]:
            raise ValueError("Invalid Listing Type. Must be one of sell, rent, others")
        return value

    @validator("property_type")
    def validate_property_type(cls, value):
        if value not in [property_type.value for property_type in ResidentialType]:
            raise ValueError(
                "Invalid Property Type. Must be one of apartment, flat, farm_house, villa"
            )
        return value

    @validator("furnishing")
    def validate_furnishing(cls, value):
        if value not in [furnishing.value for furnishing in Furnishing]:
            raise ValueError(
                "Invalid Furnishing. Must be one of furnished, semi_furnished, unfurnished"
            )
        return value

    @validator("facing")
    def validate_facing(cls, value):
        if value not in [facing.value for facing in Facing]:
            raise ValueError(
                "Invalid Facing. Must be one of north, east, west, south, north_east, north_west, south_east, south_west"
            )
        return value

    @validator("possession_type")
    def validate_possession_type(cls, value):
        if value not in [possession_type.value for possession_type in PossessionType]:
            raise ValueError(
                "Invalid Possession Type. Must be one of ready_to_move, under_construction, others"
            )
        return value

    @validator("listed_by")
    def validate_listed_by(cls, value):
        if value not in [listed_by.value for listed_by in ListedBy]:
            raise ValueError("Invalid Listed By. Must be one of broker, owner")
        return value


class ResidentialPropertySchema(CustomBaseSchema):
    property_id: str
    property_type: str
    bedrooms: int
    bathrooms: int
    furnishing: str
    built_up_area: float
    carpet_area: float
    maintenance: float
    floor_no: int
    car_parking: int
    facing: str
    balcony: bool

    @validator("property_type")
    def validate_property_type(cls, value):
        if value not in [property_type.value for property_type in ResidentialType]:
            raise ValueError(
                "Invalid Property Type. Must be one of apartment, builder_floors, farm_house, villa"
            )
        return value

    @validator("furnishing")
    def validate_furnishing(cls, value):
        if value not in [furnishing.value for furnishing in Furnishing]:
            raise ValueError(
                "Invalid Furnishing. Must be one of furnished, semi_furnished, unfurnished"
            )
        return value

    @validator("facing")
    def validate_facing(cls, value):
        if value not in [facing.value for facing in Facing]:
            raise ValueError(
                "Invalid Facing. Must be one of north, east, west, south, north_east, north_west, south_east, south_west"
            )
        return value


class FarmPropertyRequestSchema(CustomBaseSchema):
    is_investment_property: bool = False
    region_id: str
    listing_type: str
    property_type: str
    listed_by: str
    length: float
    breadth: float
    plot_area: float
    facing: str
    possession_type: str
    description: str
    project_title: str
    price: float
    video_url: str
    address: str
    location: LocationSchema
    roi_percentage: float

    @validator("listing_type")
    def validate_listing_type(cls, value):
        if value not in [listing_type.value for listing_type in ListingType]:
            raise ValueError("Invalid Listing Type. Must be one of sell, rent, others")
        return value

    @validator("facing")
    def validate_facing(cls, value):
        if value not in [facing.value for facing in Facing]:
            raise ValueError(
                "Invalid Facing. Must be one of north, east, west, south, north_east, north_west, south_east, south_west"
            )
        return value

    @validator("possession_type")
    def validate_possession_type(cls, value):
        if value not in [possession_type.value for possession_type in PossessionType]:
            raise ValueError(
                "Invalid Possession Type. Must be one of ready_to_move, under_construction, others"
            )
        return value

    @validator("listed_by")
    def validate_listed_by(cls, value):
        if value not in [listed_by.value for listed_by in ListedBy]:
            raise ValueError("Invalid Listed By. Must be one of broker, owner")
        return value


class FarmPropertySchema(CustomBaseSchema):
    property_id: str
    property_type: str
    plot_area: float
    length: float
    breadth: float
    facing: str

    @validator("facing")
    def validate_facing(cls, value):
        if value not in [facing.value for facing in Facing]:
            raise ValueError(
                "Invalid Facing. Must be one of north, east, west, south, north_east, north_west, south_east, south_west"
            )
        return value


class CommercialPropertyRequestSchema(CustomBaseSchema):
    is_investment_property: bool = False
    region_id: str
    listing_type: str
    listed_by: str
    property_type: str
    bathrooms: int
    furnishing: str
    built_up_area: float
    carpet_area: float
    maintenance: float
    car_parking: int
    facing: str
    possession_type: str
    description: str
    project_title: str
    price: float
    video_url: str
    address: str
    location: LocationSchema
    roi_percentage: float

    @validator("listing_type")
    def validate_listing_type(cls, value):
        if value not in [listing_type.value for listing_type in ListingType]:
            raise ValueError("Invalid Listing Type. Must be one of sell, rent, others")
        return value

    @validator("furnishing")
    def validate_furnishing(cls, value):
        if value not in [furnishing.value for furnishing in Furnishing]:
            raise ValueError(
                "Invalid Furnishing. Must be one of furnished, semi_furnished, unfurnished"
            )
        return value

    @validator("facing")
    def validate_facing(cls, value):
        if value not in [facing.value for facing in Facing]:
            raise ValueError(
                "Invalid Facing. Must be one of north, east, west, south, north_east, north_west, south_east, south_west"
            )
        return value

    @validator("possession_type")
    def validate_possession_type(cls, value):
        if value not in [possession_type.value for possession_type in PossessionType]:
            raise ValueError(
                "Invalid Possession Type. Must be one of ready_to_move, under_construction, others"
            )
        return value

    @validator("listed_by")
    def validate_listed_by(cls, value):
        if value not in [listed_by.value for listed_by in ListedBy]:
            raise ValueError("Invalid Listed By. Must be one of broker, owner")
        return value


class CommercialPropertySchema(CustomBaseSchema):
    property_id: str
    property_type: str
    furnishing: str
    built_up_area: float
    carpet_area: float
    maintenance: float
    car_parking: int
    bathrooms: int

    @validator("furnishing")
    def validate_furnishing(cls, value):
        if value not in [furnishing.value for furnishing in Furnishing]:
            raise ValueError(
                "Invalid Furnishing. Must be one of furnished, semi_furnished, unfurnished"
            )
        return value



class CandleData(BaseModel):
    timestamp: float = time.time()
    price: float


class CandleDataSchema(CustomBaseSchema):
    property_id: str
    property_gain: float
    candle_data: list[CandleData]

class UpdateCandleDataSchema(BaseModel):
    property_id: str
    candle_data: list[CandleData]