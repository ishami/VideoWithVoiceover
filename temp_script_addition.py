
    # GET method handling - render the script template
    else:
        # Try to get the current/latest project for this user
        project = Project.query.filter_by(
            user_id=current_user.id
        ).order_by(Project.created_at.desc()).first()
        
        # Get script content - either from the project or from session/engine
        script_content = ""
        if project and project.script:
            script_content = project.script
        else:
            # Try to get from engine or session if available
            try:
                script_content = engine.get_current_script() if hasattr(engine, 'get_current_script') else ""
            except:
                script_content = ""
        
        # Get keywords from session if available
        keywords = session.get('keywords', [])
        keywords_str = ', '.join(keywords) if keywords else ''
        
        return render_template('script.html', 
                             script=script_content,
                             project=project,
                             keywords=keywords_str)
