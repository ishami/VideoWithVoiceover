
# Updated clips route to handle project_id parameter
@app.route('/clips')
@login_required
def clips():
    """Clips/Video segments page"""
    project_id = request.args.get('project_id')
    
    if project_id:
        # Get specific project by ID
        project = Project.query.get(project_id)
        # Verify user owns this project
        if project and project.user_id != current_user.id:
            project = None
    else:
        # Get the latest project for this user
        project = Project.query.filter_by(
            user_id=current_user.id
        ).order_by(Project.created_at.desc()).first()
    
    return render_template('clips.html', project=project)
