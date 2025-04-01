import os
import shutil
import yaml
from jinja2 import Template

required_fields = ['title', 'tags', 'summary', 'logo', 'description']
community_fields = ['install_code', 'verify_code', 'deploy_code']
allowed_fields = ['title', 'tags', 'summary', 'logo', 'description', 'install_code', 'verify_code',
                  'deploy_code', 'type', 'support_link', 'doc_link', 'test_namespace', 'use_ingress', 'support_type']
allowed_tags = ['AI/Machine Learning', 'Monitoring', 'Networking', 'Security',
                'Storage', 'CI/CD', 'Application Runtime', 'Drivers and plugins', 'Backup and Recovery',
                'Authentication', 'Database', 'Developer Tools', 'Serverless', 'Enterprise']
allowed_support_types = ['Enterprise', 'Community']

def changed(file, content):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            if f.read() == content:
                return False
    return True


def validate_metadata(file: str, data: dict):
    support_type = data.get('support_type', 'Community')
    if support_type not in allowed_support_types:
        raise Exception(f"No allowed support_type found '{support_type}' in {file}, use ({allowed_support_types})")

    for required_field in required_fields:
        if required_field not in data:
            raise Exception(f"Required field '{required_field}' not found in {file}")

    if support_type == 'Community':
        for community_field in community_fields:
            if community_field not in data:
                raise Exception(f"Community field '{community_field}' not found in {file}")
    else:
        data['tags'].append(support_type)
        for community_field in community_fields:
            if community_field in data:
                raise Exception(f"Community field '{community_field}' found in Enterprise app {file}")

    for field in data:
        if field not in allowed_fields:
            raise Exception(f"Data field '{field}' from {file} not allowed")

    if not isinstance(data['tags'], list):
        raise Exception(f"Field 'tags' needs to be an array! ({file})")
    for tag in data['tags']:
        if tag not in allowed_tags:
            raise Exception(f"Unsupported tag '{tag}' found in {file}. Allowed tags: {allowed_tags}")

    if data.get('type', 'app') != 'infra' and len(data['tags']) == 0:
        raise Exception(f"No application tag found in {file}. Set at least one from tags: {allowed_tags}")


def try_copy_assets(app: str, apps_dir: str, dst_dir: str):
    src_dir = os.path.join(apps_dir, app, "assets")
    dst_dir = os.path.join(dst_dir, "apps", app, "assets")
    if os.path.exists(src_dir) and os.path.isdir(src_dir):
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        print(f"Assets copied from {src_dir} to {dst_dir}")


def generate_apps():
    apps_dir = 'apps'
    dst_dir = 'mkdocs'
    template_path = 'mkdocs/app.tpl.md'

    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    template = Template(template_content)

    # Iterate over each app directory
    for app in os.listdir(apps_dir):
        app_path = os.path.join(apps_dir, app)
        dst_app_path = os.path.join(dst_dir, app_path)
        if not os.path.exists(dst_app_path):
            os.makedirs(dst_app_path)
        data_file = os.path.join(app_path, 'data.yaml')
        md_file = os.path.join(dst_app_path, app + '.md')
        try_copy_assets(app, apps_dir, dst_dir)
        if os.path.isdir(app_path) and os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f)
                validate_metadata(data_file, metadata)

            # Render the template with metadata
            rendered_md = template.render(**metadata)

            if changed(md_file, rendered_md):
                # Write the generated markdown
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(rendered_md)

generate_apps()
