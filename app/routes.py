from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, LostItem, FoundItem, Claim
from datetime import datetime
from sqlalchemy import or_, and_

# Authentication routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_number = request.form.get('id_number')  # 學號或編號
        email = request.form.get('email')
        password = request.form.get('password')
        real_name = request.form.get('real_name')
        role = request.form.get('role', 'student')
        
        # 驗證身份編號
        if not id_number:
            flash('必須填寫學號或編號', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(id_number=id_number).first():
            flash('此學號或編號已被使用', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('電郵已被使用', 'error')
            return redirect(url_for('auth.register'))
        
        user = User(
            id_number=id_number,
            email=email, 
            real_name=real_name, 
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('註冊成功，請登入', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id_number = request.form.get('id_number')  # 學號或編號
        password = request.form.get('password')
        
        user = User.query.filter_by(id_number=id_number).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('學號/編號或密碼錯誤', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已登出', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理員登入入口 - 需要額外的安全檢查"""
    if request.method == 'POST':
        id_number = request.form.get('id_number')
        password = request.form.get('password')
        
        user = User.query.filter_by(id_number=id_number).first()
        
        # 驗證用戶存在、密碼正確且為管理員
        if not user:
            flash('學號/編號不存在', 'error')
            return redirect(url_for('auth.admin_login'))
        
        if not user.check_password(password):
            flash('密碼錯誤', 'error')
            return redirect(url_for('auth.admin_login'))
        
        if user.role != 'admin':
            # 安全日誌：非管理員嘗試通過管理員入口登入
            flash('您無權訪問管理員入口', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        flash('管理員登入成功', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('auth/admin_login.html')


# Main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    lost_count = LostItem.query.filter_by(status='lost').count()
    found_count = FoundItem.query.filter_by(status='available').count()
    return render_template('index.html', lost_count=lost_count, found_count=found_count)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    my_lost = LostItem.query.filter_by(reporter_id=current_user.id).all()
    my_found = FoundItem.query.filter_by(finder_id=current_user.id).all()
    my_claims = Claim.query.filter_by(claimer_id=current_user.id).all()
    
    return render_template('dashboard.html', 
                         my_lost=my_lost, 
                         my_found=my_found,
                         my_claims=my_claims)


# Lost items routes
lost_items_bp = Blueprint('lost_items', __name__, url_prefix='/lost')

@lost_items_bp.route('/list')
def list_lost():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = LostItem.query.filter_by(status='lost')
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(or_(
            LostItem.title.ilike(f'%{search}%'),
            LostItem.description.ilike(f'%{search}%'),
            LostItem.location.ilike(f'%{search}%')
        ))
    
    items = query.order_by(LostItem.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('lost/list.html', items=items, category=category, search=search)


@lost_items_bp.route('/detail/<int:item_id>')
def detail_lost(item_id):
    item = LostItem.query.get_or_404(item_id)
    matching_found = FoundItem.query.filter_by(status='available', category=item.category).limit(5).all()
    
    return render_template('lost/detail.html', item=item, matching_found=matching_found)


@lost_items_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report_lost():
    # 一般用戶（學生、教職員）可以報告自己遺失的物品
    if current_user.role == 'admin':
        flash('管理員不能報告失物', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        lost_date = request.form.get('lost_date')
        contact_phone = request.form.get('contact_phone')
        
        try:
            lost_date = datetime.fromisoformat(lost_date)
        except:
            flash('日期格式錯誤', 'error')
            return redirect(url_for('lost_items.report_lost'))
        
        item = LostItem(
            title=title,
            description=description,
            category=category,
            location=location,
            lost_date=lost_date,
            reporter_id=current_user.id,
            contact_phone=contact_phone
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('失物報告已提交', 'success')
        return redirect(url_for('main.dashboard'))
    
    categories = ['電話', '錢包', '鑰匙', '衣服', '眼鏡', '書包', '其他']
    return render_template('lost/report.html', categories=categories)


@lost_items_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_lost(item_id):
    item = LostItem.query.get_or_404(item_id)
    
    # 只有報告者（一般用戶）可以編輯自己的失物
    if item.reporter_id != current_user.id:
        flash('您沒有權限編輯此項目', 'error')
        return redirect(url_for('lost_items.detail_lost', item_id=item_id))
    
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.description = request.form.get('description')
        item.category = request.form.get('category')
        item.location = request.form.get('location')
        item.contact_phone = request.form.get('contact_phone')
        item.status = request.form.get('status')
        
        db.session.commit()
        flash('失物信息已更新', 'success')
        return redirect(url_for('lost_items.detail_lost', item_id=item_id))
    
    categories = ['電話', '錢包', '鑰匙', '衣服', '眼鏡', '書包', '其他']
    return render_template('lost/edit.html', item=item, categories=categories)


@lost_items_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_lost(item_id):
    item = LostItem.query.get_or_404(item_id)
    
    # 只有報告者可以刪除自己的失物
    if item.reporter_id != current_user.id:
        flash('您沒有權限刪除此項目', 'error')
    else:
        db.session.delete(item)
        db.session.commit()
        flash('失物記錄已刪除', 'success')
    
    return redirect(url_for('main.dashboard'))


# Found items routes
found_items_bp = Blueprint('found_items', __name__, url_prefix='/found')

@found_items_bp.route('/list')
def list_found():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = FoundItem.query
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(or_(
            FoundItem.title.ilike(f'%{search}%'),
            FoundItem.description.ilike(f'%{search}%'),
            FoundItem.location.ilike(f'%{search}%')
        ))
    
    items = query.order_by(FoundItem.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('found/list.html', items=items, category=category, search=search)


@found_items_bp.route('/detail/<int:item_id>')
def detail_found(item_id):
    item = FoundItem.query.get_or_404(item_id)
    return render_template('found/detail.html', item=item)


@found_items_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report_found():
    # 只有管理員可以報告拾物
    if current_user.role != 'admin':
        flash('只有管理員可以上傳拾物', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        found_date = request.form.get('found_date')
        contact_phone = request.form.get('contact_phone')
        
        try:
            found_date = datetime.fromisoformat(found_date)
        except:
            flash('日期格式錯誤', 'error')
            return redirect(url_for('found_items.report_found'))
        
        item = FoundItem(
            title=title,
            description=description,
            category=category,
            location=location,
            found_date=found_date,
            finder_id=current_user.id,
            contact_phone=contact_phone
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('拾物報告已提交', 'success')
        return redirect(url_for('main.dashboard'))
    
    categories = ['電話', '錢包', '鑰匙', '衣服', '眼鏡', '書包', '其他']
    return render_template('found/report.html', categories=categories)


@found_items_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_found(item_id):
    item = FoundItem.query.get_or_404(item_id)
    
    # 只有管理員可以編輯拾物
    if current_user.role != 'admin':
        flash('只有管理員可以編輯拾物', 'error')
        return redirect(url_for('found_items.detail_found', item_id=item_id))
    
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.description = request.form.get('description')
        item.category = request.form.get('category')
        item.location = request.form.get('location')
        item.contact_phone = request.form.get('contact_phone')
        item.status = request.form.get('status')
        
        db.session.commit()
        flash('拾物信息已更新', 'success')
        return redirect(url_for('found_items.detail_found', item_id=item_id))
    
    categories = ['電話', '錢包', '鑰匙', '衣服', '眼鏡', '書包', '其他']
    return render_template('found/edit.html', item=item, categories=categories)


@found_items_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_found(item_id):
    item = FoundItem.query.get_or_404(item_id)
    
    # 只有管理員可以刪除拾物
    if current_user.role != 'admin':
        flash('只有管理員可以刪除拾物', 'error')
    else:
        db.session.delete(item)
        db.session.commit()
        flash('拾物記錄已刪除', 'success')
    
    return redirect(url_for('main.dashboard'))


# Claims routes
claims_bp = Blueprint('claims', __name__, url_prefix='/claims')

@claims_bp.route('/create', methods=['POST'])
@login_required
def create_claim():
    lost_item_id = request.form.get('lost_item_id')
    found_item_id = request.form.get('found_item_id')
    
    if not lost_item_id or not found_item_id:
        flash('請選擇協尋記錄', 'danger')
        return redirect(url_for('found_items.detail_found', item_id=found_item_id))
        
    lost_id = int(lost_item_id)
    found_id = int(found_item_id)
    
    lost = LostItem.query.get_or_404(lost_id)
    found = FoundItem.query.get_or_404(found_id)
    
    # Check if claim already exists
    existing = Claim.query.filter_by(
        lost_item_id=lost_id,
        found_item_id=found_id,
        claimer_id=current_user.id
    ).first()
    
    if existing:
        flash('您已提交過此認領登記', 'warning')
        return redirect(url_for('found_items.detail_found', item_id=found_id))
    
    claim = Claim(
        lost_item_id=lost_id,
        found_item_id=found_id,
        claimer_id=current_user.id,
        proof_description=f'使用者 {current_user.real_name} 認為遺失物 #{found_id} 是他登記的協尋物 #{lost_id}',
        status='pending'
    )
    
    db.session.add(claim)
    
    # Update found item status
    found.status = 'claimed'
    
    db.session.commit()
    
    flash('認領登記已提交，請等待管理員審核', 'success')
    return redirect(url_for('main.dashboard'))


@claims_bp.route('/approve/<int:claim_id>', methods=['POST'])
@login_required
def approve_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    found = claim.found_item
    lost = claim.lost_item
    
    if found.finder_id != current_user.id:
        flash('您沒有權限批准此認領', 'error')
        return redirect(url_for('main.dashboard'))
    
    claim.status = 'approved'
    lost.status = 'found'
    found.status = 'claimed'
    
    db.session.commit()
    flash('認領申請已批准', 'success')
    
    return redirect(url_for('main.dashboard'))


@claims_bp.route('/returned/<int:claim_id>', methods=['POST'])
@login_required
def returned_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    
    if claim.claimer_id != current_user.id:
        flash('您沒有權限確認領取此物品', 'error')
        return redirect(url_for('main.dashboard'))
    
    claim.status = 'returned'
    # 也可以更新失物或拾物的狀態如果需要，但先更新申請狀態
    claim.found_item.status = 'returned'
    claim.lost_item.status = 'claimed'
    db.session.commit()
    
    flash('已確認領取，謝謝！', 'success')
    return redirect(url_for('main.dashboard'))

@claims_bp.route('/notify/<int:lost_id>', methods=['POST'])
@login_required
def notify_lost(lost_id):
    lost = LostItem.query.get_or_404(lost_id)
    
    if current_user.role != 'admin':
        flash('只有管理員可以發送通知', 'error')
        return redirect(url_for('main.dashboard'))
    
    # 這裡可以用寄信的邏輯，但我們先用 flash 模擬寄信通知，並將失物狀態改變，
    # 代表已經通知
    lost.status = 'notified'
    db.session.commit()
    
    flash('失物領取通知已寄出（模擬），已通知同學領取！', 'success')
    return redirect(url_for('main.dashboard'))

