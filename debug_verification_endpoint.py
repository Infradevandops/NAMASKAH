# Enhanced verification creation with better error handling
@app.post(
    "/verify/create/debug",
    tags=["Verification"],
    summary="Debug SMS/Voice Verification Creation",
)
def create_verification_debug(
    req: CreateVerificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Debug version of verification creation with detailed error reporting"""

    debug_info = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user.id,
        "service_name": req.service_name,
        "capability": req.capability,
        "steps": [],
    }

    try:
        # Step 1: Validate TextVerified configuration
        debug_info["steps"].append("Checking TextVerified configuration...")

        if not TEXTVERIFIED_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="TextVerified API key not configured. Please set TEXTVERIFIED_API_KEY in environment variables.",
            )

        if not TEXTVERIFIED_EMAIL:
            raise HTTPException(
                status_code=503,
                detail="TextVerified email not configured. Please set TEXTVERIFIED_EMAIL in environment variables.",
            )

        debug_info["steps"].append("✅ TextVerified configuration OK")

        # Step 2: Check user credits and subscription
        debug_info["steps"].append("Checking user credits and subscription...")

        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == user.id, Subscription.status == "active")
            .first()
        )
        user_plan = subscription.plan if subscription else "starter"

        # Get monthly verification count
        month_start = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0
        )
        monthly_count = (
            db.query(Verification)
            .filter(
                Verification.user_id == user.id, Verification.created_at >= month_start
            )
            .count()
        )

        # Calculate cost
        cost = get_service_price(req.service_name, user_plan, monthly_count)
        if req.capability == "voice":
            cost += VOICE_PREMIUM

        debug_info["calculated_cost"] = cost
        debug_info["user_credits"] = user.credits
        debug_info["free_verifications"] = user.free_verifications

        # Check if user can afford
        plan_data = SUBSCRIPTION_PLANS[user_plan]
        free_limit = plan_data.get("free_verifications", 0)

        can_use_free = free_limit == -1 or (
            user.free_verifications > 0 and free_limit > 0
        )

        if can_use_free:
            debug_info["steps"].append("✅ Using free verification")
            cost = 0
        elif user.credits < cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Need N{cost}, have N{user.credits}. Free verifications: {user.free_verifications}",
            )

        debug_info["steps"].append("✅ Credit check passed")

        # Step 3: Test TextVerified API connection
        debug_info["steps"].append("Testing TextVerified API connection...")

        try:
            # Test authentication
            token = tv_client.get_token()
            debug_info["steps"].append("✅ TextVerified authentication successful")
            debug_info["textverified_token"] = token[:20] + "..." if token else None

        except Exception as e:
            debug_info["steps"].append(
                f"❌ TextVerified authentication failed: {str(e)}"
            )
            raise HTTPException(
                status_code=503,
                detail=f"TextVerified API authentication failed: {str(e)}. Please check your API credentials.",
            )

        # Step 4: Create verification
        debug_info["steps"].append("Creating verification with TextVerified...")

        try:
            verification_id = tv_client.create_verification(
                req.service_name,
                req.capability,
                area_code=req.area_code,
                carrier=req.carrier,
            )

            if not verification_id:
                raise Exception("No verification ID returned from TextVerified")

            debug_info["textverified_verification_id"] = verification_id
            debug_info["steps"].append("✅ TextVerified verification created")

        except Exception as e:
            debug_info["steps"].append(
                f"❌ TextVerified verification creation failed: {str(e)}"
            )
            raise HTTPException(
                status_code=503,
                detail=f"Failed to create verification with TextVerified: {str(e)}",
            )

        # Step 5: Get verification details
        debug_info["steps"].append("Getting verification details...")

        try:
            details = tv_client.get_verification(verification_id)
            phone_number = details.get("number")

            if not phone_number:
                raise Exception("No phone number returned from TextVerified")

            debug_info["phone_number"] = phone_number
            debug_info["steps"].append("✅ Phone number retrieved")

        except Exception as e:
            debug_info["steps"].append(
                f"❌ Failed to get verification details: {str(e)}"
            )
            raise HTTPException(
                status_code=503, detail=f"Failed to get verification details: {str(e)}"
            )

        # Step 6: Save to database
        debug_info["steps"].append("Saving verification to database...")

        try:
            # Deduct credits if not free
            if cost > 0:
                user.credits -= cost
            else:
                user.free_verifications -= 1

            # Create verification record
            verification = Verification(
                id=verification_id,
                user_id=user.id,
                service_name=req.service_name,
                phone_number=phone_number,
                capability=req.capability,
                status="pending",
                cost=cost,
                requested_carrier=req.carrier,
                requested_area_code=req.area_code,
            )

            db.add(verification)

            # Create transaction if cost > 0
            if cost > 0:
                tier = get_service_tier(req.service_name)
                db.add(
                    Transaction(
                        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                        user_id=user.id,
                        amount=-cost,
                        type="debit",
                        description=f"{req.service_name} verification ({tier})",
                    )
                )

            db.commit()
            debug_info["steps"].append("✅ Database save successful")

        except Exception as e:
            debug_info["steps"].append(f"❌ Database save failed: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save verification to database: {str(e)}",
            )

        # Success response
        debug_info["steps"].append("✅ Verification creation completed successfully")

        return {
            "success": True,
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": cost,
            "remaining_credits": user.credits,
            "debug_info": debug_info,
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors
        debug_info["steps"].append(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during verification creation: {str(e)}",
            headers={"X-Debug-Info": json.dumps(debug_info)},
        )
