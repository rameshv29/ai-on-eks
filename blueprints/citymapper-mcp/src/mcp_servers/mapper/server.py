#!/usr/bin/env python3
"""
Mapper Service - Route optimization and interactive HTML generation
Provides HTTP endpoints for travel plan generation and route optimization
"""
import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Citymapper Mapper Service", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mapper-service"}

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Citymapper Mapper Service",
        "version": "1.0.0",
        "description": "Route optimization and interactive HTML generation",
        "endpoints": {
            "/health": "Health check",
            "/generate": "Generate travel plan",
            "/optimize": "Optimize routes"
        }
    }

@app.post("/generate")
async def generate_travel_plan(request: Dict[str, Any]):
    """Generate interactive travel plan"""
    try:
        city = request.get("city", "san_francisco")
        days = request.get("days", 4)
        focus = request.get("focus", "balanced")
        use_services = request.get("use_services", True)
        
        logger.info(f"Generating travel plan for {city}, {days} days, {focus} focus")
        
        # Import and run the travel planner
        try:
            import subprocess
            import json
            
            # Build command to run interactive travel planner
            cmd = [
                "python", 
                "/app/scripts/interactive_travel_planner.py",
                "--use-services" if use_services else "",
                "--city", city,
                "--days", str(days),
                "--focus", focus
            ]
            
            # Remove empty strings
            cmd = [arg for arg in cmd if arg]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            # Run the travel planner
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                # Parse output to extract file info and S3 URL
                output = result.stdout
                
                # Extract filename, S3 URL, file size, and expiry
                filename = None
                s3_url = None
                expires_at = None
                file_size = None
                
                for line in output.split('\n'):
                    if "Interactive plan saved:" in line:
                        filename = line.split(': ')[-1].strip()
                    elif "DOWNLOAD LINK (Valid for 30 minutes):" in line:
                        # Next line should contain the URL
                        continue
                    elif line.strip().startswith("https://"):
                        s3_url = line.strip()
                    elif "Link expires at:" in line:
                        expires_at = line.split(': ')[-1].strip()
                    elif "File:" in line and "bytes" in line:
                        # Extract file size from lines like "File: filename.html (32,537 bytes)"
                        try:
                            size_part = line.split('(')[-1].split(' bytes')[0]
                            file_size = size_part.replace(',', '')
                        except:
                            pass
                
                return {
                    "status": "success",
                    "message": f"Travel plan generated for {city}",
                    "city": city,
                    "days": days,
                    "focus": focus,
                    "filename": filename,
                    "s3_url": s3_url,
                    "expires_at": expires_at,
                    "file_size": file_size,
                    "output_preview": output[:500] + "..." if len(output) > 500 else output
                }
            else:
                logger.error(f"Travel planner failed: {result.stderr}")
                raise HTTPException(status_code=500, detail=f"Travel planner failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=500, detail="Travel plan generation timed out")
        except Exception as e:
            logger.error(f"Error generating travel plan: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate travel plan: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error in generate_travel_plan: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/optimize")
async def optimize_routes(request: Dict[str, Any]):
    """Optimize routes for given locations"""
    try:
        locations = request.get("locations", [])
        if not locations:
            raise HTTPException(status_code=400, detail="No locations provided")
            
        logger.info(f"Optimizing routes for {len(locations)} locations")
        
        # Simple route optimization logic (placeholder)
        optimized_routes = {
            "status": "success",
            "original_locations": locations,
            "optimized_order": list(range(len(locations))),
            "total_distance": "calculated",
            "estimated_time": "calculated"
        }
        
        return optimized_routes
        
    except Exception as e:
        logger.error(f"Error in optimize_routes: {e}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    logger.info("🗺️ Starting Citymapper Mapper Service...")
    logger.info("📍 Route optimization and HTML generation service")
    logger.info("🌐 Available endpoints: /health, /generate, /optimize")
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8007,
        log_level="info"
    )
