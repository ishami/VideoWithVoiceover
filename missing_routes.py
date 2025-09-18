
# ========================================================================
# Missing Navigation Routes
# ========================================================================

@app.route('/clips')
@login_required
def clips():
    """Clips/Video segments page"""
    # Try to get the current project
    project = Project.query.filter_by(
        user_id=current_user.id
    ).order_by(Project.created_at.desc()).first()
    
    return render_template('clips.html', project=project)

@app.route('/final_video')
@login_required  
def final_video():
    """Final video page"""
    # Try to get the current project
    project = Project.query.filter_by(
        user_id=current_user.id
    ).order_by(Project.created_at.desc()).first()
    
    return render_template('final_video.html', project=project)

@app.route('/support')
def support():
    """Support/Help page"""
    return render_template('support.html')
