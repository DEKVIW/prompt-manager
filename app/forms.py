from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(), 
        Length(1, 64),
        Regexp('^[A-Za-z0-9_]*$', 0, '用户名只能包含字母、数字和下划线')
    ])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[
        DataRequired(), 
        Length(8, 128, message='密码长度必须至少为8个字符')
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(), 
        EqualTo('password', message='两次输入的密码必须匹配')
    ])
    invite_code = StringField('邀请码', validators=[DataRequired()])
    submit = SubmitField('注册')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被使用')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')

class PromptForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 100)])
    content = TextAreaField('提示词内容', validators=[DataRequired()])
    description = TextAreaField('描述')
    version = StringField('版本', default='1.0')
    tags = StringField('标签 (用逗号分隔)')
    cover_image = FileField('封面图片', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], '只允许上传图片文件!')
    ])
    is_public = BooleanField('公开分享', default=False)
    submit = SubmitField('保存')

class InviteCodeForm(FlaskForm):
    quantity = SelectField('数量', choices=[(str(i), str(i)) for i in range(1, 11)], default='1')
    submit = SubmitField('生成邀请码') 