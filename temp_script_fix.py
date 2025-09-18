# Add this logic before the render_template call in the GET request section

# GET request - load existing keywords if available
keywords = []
keywords_path = os.path.join('workspace', 'keywords.txt')
if os.path.exists(keywords_path):
    with open(keywords_path, 'r') as f:
        keywords_text = f.read().strip()
        keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]

# Try to get current project information
project = None
project_id = request.args.get('project_id', type=int) or session.get('pending_project_id')
if project_id:
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()

return render_template('script.html',
                       script=engine.get_current_script(),
                       keywords=keywords,
                       project=project)
