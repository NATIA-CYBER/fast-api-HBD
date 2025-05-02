import os
import gzip
import json
from typing import Annotated, List, Dict, Any

from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel
from fastapi.params import Query, Path
import requests
import pandas as pd

from bdi_api.settings import Settings

settings = Settings()

s1 = APIRouter(
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Invalid request parameters"},
    },
    prefix="/s1",
    tags=["s1"],
)

class Aircraft(BaseModel):
    icao: str
    registration: str | None = None
    type: str | None = None
    flight: str | None = None

class Position(BaseModel):
    icao: str
    lat: float
    lon: float
    seen: float | None = None

class Stats(BaseModel):
    icao: str
    alt_baro: float | None = None
    gs: float | None = None
    emergency: bool | None = None
    registration: str | None = None
    type: str | None = None
    flight: str | None = None

@s1.post("/aircraft/download")
def download_data(file_limit: Annotated[int, Query(...)] = 100) -> str:
    # Use settings.raw_dir directly as it already includes day=20231101
    os.makedirs(settings.raw_dir, exist_ok=True)
    
    for file in os.listdir(settings.raw_dir):
        file_path = os.path.join(settings.raw_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    base_url = settings.source_url + "/2023/11/01/"
    files_to_download = [
        "000000Z.json.gz",
        "000005Z.json.gz",
        "000010Z.json.gz",
        "000015Z.json.gz"
    ]
    
    for filename in files_to_download[:file_limit]:
        response = requests.get(f"{base_url}{filename}")
        if response.status_code == 200:
            output_path = os.path.join(settings.raw_dir, filename)
            with open(output_path, "wb") as f:
                f.write(response.content)
    
    return "OK"


@s1.post("/aircraft/prepare")
def prepare_data() -> str:
    raw_dir = settings.raw_dir
    prepared_dir = settings.prepared_dir
    
    # Clear prepared directory
    for file in os.listdir(prepared_dir):
        file_path = os.path.join(prepared_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    all_data = []
    for filename in sorted(os.listdir(raw_dir)):
        if not filename.endswith('.json.gz'):
            continue
            
        file_path = os.path.join(raw_dir, filename)
        try:
            # Try reading as gzipped first
            try:
                with gzip.open(file_path, 'rb') as f:
                    data = json.loads(f.read().decode('utf-8'))
            except Exception:
                # If that fails, try reading as plain JSON
                with open(file_path, 'r') as f:
                    data = json.load(f)
            
            if 'aircraft' in data:
                all_data.extend(data['aircraft'])
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    if not all_data:
        return "No data to process"
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(all_data)
    print(f"Available columns: {df.columns.tolist()}")
    print(f"Sample data:\n{df[['hex', 'lat', 'lon']].head()}")
    
    # Convert numeric fields
    numeric_fields = ['lat', 'lon', 'seen', 'alt_baro', 'gs']
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')
    
    # Save processed data
    aircraft_info = df[['hex', 'r', 't', 'flight']].rename(columns={
        'hex': 'icao',
        'r': 'registration',
        't': 'type'
    }).dropna(subset=['icao']).drop_duplicates('icao')
    
    # Filter positions - only require lat/lon to be present
    positions = df[df['lat'].notna() & df['lon'].notna()][['hex', 'lat', 'lon', 'seen']].rename(columns={'hex': 'icao'})
    
    stats = df.groupby('hex').agg({
        'alt_baro': lambda x: x.dropna().max() if len(x.dropna()) > 0 else None,
        'gs': lambda x: x.dropna().max() if len(x.dropna()) > 0 else None,
        'emergency': lambda x: any(str(val) == '1' for val in x.dropna())
    }).reset_index().rename(columns={'hex': 'icao'})
    
    print(f"Found {len(aircraft_info)} aircraft")
    print(f"Found {len(positions)} positions")
    print(f"Found {len(stats)} stats")
    
    # Save to files
    aircraft_info.to_parquet(os.path.join(prepared_dir, 'aircraft_info.parquet'))
    positions.to_parquet(os.path.join(prepared_dir, 'positions.parquet'))
    stats.to_parquet(os.path.join(prepared_dir, 'statistics.parquet'))
    
    return "OK"


@s1.get("/aircraft", response_model=List[Aircraft])
def list_aircraft() -> List[Dict[str, Any]]:
    """List all aircraft with their basic information."""
    try:
        df = pd.read_parquet(os.path.join(settings.prepared_dir, 'aircraft_info.parquet'))
        return df.fillna('').to_dict('records')
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No aircraft data found. Please download and prepare data first."
        )


@s1.get("/aircraft/{icao}/positions", response_model=List[Position])
def get_aircraft_positions(icao: Annotated[str, Path(description="Aircraft ICAO identifier")], num_results: int = 1000, page: int = 0) -> List[Dict[str, Any]]:
    """Get all recorded positions for a specific aircraft."""
    try:
        df = pd.read_parquet(os.path.join(settings.prepared_dir, 'positions.parquet'))
        print(f"Total positions: {len(df)}")
        positions = df[df['icao'] == icao].sort_values('seen')
        print(f"Positions for {icao}: {len(positions)}")
        
        if len(positions) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No positions found for aircraft {icao}"
            )
        
        # Apply pagination
        start_idx = page * num_results
        end_idx = start_idx + num_results
        positions = positions.iloc[start_idx:end_idx]
        
        return positions.to_dict('records')
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position data not found. Please run /aircraft/prepare first."
        )


@s1.get("/aircraft/{icao}/stats", response_model=Stats)
def get_aircraft_stats(icao: Annotated[str, Path(description="Aircraft ICAO identifier")]) -> Dict[str, Any]:
    """Get statistics for a specific aircraft."""
    try:
        df = pd.read_parquet(os.path.join(settings.prepared_dir, 'statistics.parquet'))
        stats = df[df['icao'] == icao]
        
        if len(stats) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No statistics found for aircraft {icao}"
            )
        
        # Get aircraft info as well
        try:
            info_df = pd.read_parquet(os.path.join(settings.prepared_dir, 'aircraft_info.parquet'))
            info = info_df[info_df['icao'] == icao].iloc[0].to_dict()
        except Exception:
            info = {}
        
        # Combine stats and info
        result = stats.iloc[0].to_dict()
        result.update(info)
        
        return result
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statistics data not found. Please run /aircraft/prepare first."
        )



