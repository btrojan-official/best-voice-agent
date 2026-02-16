import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from models import (
    db, LoginRequest, LoginResponse, SettingsUpdateRequest,
    InformationToGatherRequest, Call, Settings, SystemStats
)
from auth import AuthService, require_auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Admin login endpoint.
    
    Args:
        request: Login credentials
    
    Returns:
        Login response with token
    """
    try:
        if AuthService.verify_credentials(request.username, request.password):
            token = AuthService.create_token(request.username)
            logger.info(f"Successful login for user: {request.username}")
            
            return LoginResponse(
                success=True,
                token=token,
                message="Login successful"
            )
        else:
            logger.warning(f"Failed login attempt for user: {request.username}")
            return LoginResponse(
                success=False,
                message="Invalid credentials"
            )
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls", response_model=List[Call])
async def get_all_calls(token: str = Depends(require_auth)):
    """
    Get all calls.
    
    Returns:
        List of all calls
    """
    try:
        calls = await db.get_all_calls()
        calls_sorted = sorted(calls, key=lambda x: x.start_time, reverse=True)
        logger.info(f"Retrieved {len(calls)} calls")
        return calls_sorted
    
    except Exception as e:
        logger.error(f"Error retrieving calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}", response_model=Call)
async def get_call_details(call_id: str, token: str = Depends(require_auth)):
    """
    Get detailed information about a specific call.
    
    Args:
        call_id: Call ID
    
    Returns:
        Call details
    """
    try:
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        logger.info(f"Retrieved details for call {call_id}")
        return call
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving call details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/calls/{call_id}")
async def delete_call(call_id: str, token: str = Depends(require_auth)):
    """
    Delete a call.
    
    Args:
        call_id: Call ID
    
    Returns:
        Success message
    """
    try:
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        logger.info(f"Call {call_id} deletion requested (not implemented)")
        
        return {"success": True, "message": "Call deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SystemStats)
async def get_stats(token: str = Depends(require_auth)):
    """
    Get system statistics.
    
    Returns:
        System statistics
    """
    try:
        stats = await db.get_stats()
        logger.info("Retrieved system statistics")
        return stats
    
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings", response_model=Settings)
async def get_settings(token: str = Depends(require_auth)):
    """
    Get current settings.
    
    Returns:
        Settings
    """
    try:
        settings = await db.get_settings()
        logger.info("Retrieved settings")
        return settings
    
    except Exception as e:
        logger.error(f"Error retrieving settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/settings")
async def update_settings(
    request: SettingsUpdateRequest,
    token: str = Depends(require_auth)
):
    """
    Update settings.
    
    Args:
        request: Settings update request
    
    Returns:
        Updated settings
    """
    try:
        settings = await db.get_settings()
        
        if request.model_name is not None:
            settings.model_name = request.model_name
        
        if request.temperature is not None:
            if not 0.0 <= request.temperature <= 2.0:
                raise HTTPException(
                    status_code=400,
                    detail="Temperature must be between 0.0 and 2.0"
                )
            settings.temperature = request.temperature
        
        updated_settings = await db.update_settings(settings)
        logger.info("Updated settings")
        
        return updated_settings
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/information")
async def add_information_to_gather(
    request: InformationToGatherRequest,
    token: str = Depends(require_auth)
):
    """
    Add new information to gather.
    
    Args:
        request: Information to gather details
    
    Returns:
        Created information item
    """
    try:
        info = await db.add_information_to_gather(
            title=request.title,
            description=request.description
        )
        logger.info(f"Added information to gather: {request.title}")
        
        return info
    
    except Exception as e:
        logger.error(f"Error adding information to gather: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/settings/information/{info_id}")
async def remove_information_to_gather(
    info_id: str,
    token: str = Depends(require_auth)
):
    """
    Remove information to gather.
    
    Args:
        info_id: Information ID
    
    Returns:
        Success message
    """
    try:
        success = await db.remove_information_to_gather(info_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Information not found")
        
        logger.info(f"Removed information to gather: {info_id}")
        
        return {"success": True, "message": "Information removed"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing information to gather: {e}")
        raise HTTPException(status_code=500, detail=str(e))
