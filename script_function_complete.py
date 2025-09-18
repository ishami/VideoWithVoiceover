@app.route('/script', methods=['GET', 'POST'])
@login_required
def script():
    if request.method == 'POST':
        script_text = request.form['script']
        title = request.form.get('title', 'Untitled')

        # Get the modified keywords from the form
        keywords = request.form.get('keywords', '')
        if keywords:
            # Save keywords to file for engine to use
            keywords_path = os.path.join('workspace', 'keywords.txt')
            with open(keywords_path, 'w') as f:
                f.write(keywords)

            # Parse keywords for engine (limit to 2-3 for performance)
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()][:3]
            session['keywords'] = keyword_list
            app.logger.info(f"Using keywords from form: {keyword_list}")

        # 1) Create draft project
        proj = Project(
            user_id=current_user.id,
            title=title,
            script=script_text,
            status='draft'
        )
        db.session.add(proj)
        db.session.commit()

        # 2) Enforce free-tier limit
        count = Project.query.filter_by(user_id=current_user.id).count()
        if count > current_user.projects_limit and not current_user.is_premium:
            # stash for resume
            session['pending_project_id'] = proj.id
            # redirect user to your upgrade page
            upgrade_url = url_for('payments.upgrade')
            return jsonify({
                'success': False,
                'message': f"Free tier limited to {current_user.projects_limit}.",
                'upgrade_url': upgrade_url
            }), 402

        # 3) Mark processing and kick off your worker
        proj.status = 'processing'
        db.session.commit()

        # Clear old media before regeneration
        clear_old_media()

        ok, msg = engine.save_script_and_regenerate(script_text, current_user.id)

        return jsonify({
            'success': ok,
            'message': msg,
            'project_id': proj.id
        })

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
