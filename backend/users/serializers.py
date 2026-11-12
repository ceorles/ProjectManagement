from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User


def _validate_password(password, user=None):
    try:
        password_validation.validate_password(password, user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return password


def _unique_email(value, instance=None):
    email = value.strip().lower()
    queryset = User.objects.filter(email__iexact=email)
    if instance is not None:
        queryset = queryset.exclude(pk=instance.pk)
    if queryset.exists():
        raise serializers.ValidationError('An account with this email already exists.')
    return email


def _unique_student_id(value, instance=None):
    student_id = (value or '').strip()
    if not student_id:
        return None
    queryset = User.objects.filter(student_id__iexact=student_id)
    if instance is not None:
        queryset = queryset.exclude(pk=instance.pk)
    if queryset.exists():
        raise serializers.ValidationError('This student ID is already registered.')
    return student_id


class UserSerializer(serializers.ModelSerializer):
    """The signed-in user's own account, as returned by the auth endpoints."""

    full_name = serializers.CharField(read_only=True)
    can_manage_resources = serializers.BooleanField(
        source='can_manage_library_resources', read_only=True
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'role',
            'student_id', 'program', 'year_level', 'phone',
            'can_manage_resources', 'date_joined',
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Public self-registration. Always creates a Student, whatever is sent."""

    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
    student_id = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'student_id', 'program',
            'year_level', 'phone', 'password', 'confirm_password',
        ]

    def validate_email(self, value):
        return _unique_email(value)

    def validate_student_id(self, value):
        for validator in User._meta.get_field('student_id').validators:
            try:
                validator(value.strip())
            except DjangoValidationError as exc:
                raise serializers.ValidationError(list(exc.messages)) from exc
        return _unique_student_id(value)

    def validate_year_level(self, value):
        if value is not None and not 1 <= value <= 8:
            raise serializers.ValidationError('Year level must be between 1 and 8.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        candidate = User(
            email=attrs['email'], first_name=attrs['first_name'], last_name=attrs['last_name']
        )
        try:
            _validate_password(attrs['password'], candidate)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({'password': exc.detail}) from exc
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(
            password=password, role=User.Role.STUDENT, **validated_data
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """What a user may change about their own account."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'program', 'year_level']

    def validate_year_level(self, value):
        if value is not None and not 1 <= value <= 8:
            raise serializers.ValidationError('Year level must be between 1 and 8.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(trim_whitespace=False)
    confirm_password = serializers.CharField(trim_whitespace=False)

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Your current password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        try:
            _validate_password(attrs['new_password'], self.context['request'].user)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({'new_password': exc.detail}) from exc
        return attrs


class ManagedUserSerializer(serializers.ModelSerializer):
    """Accounts as seen and edited by an Admin."""

    full_name = serializers.CharField(read_only=True)
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'role',
            'student_id', 'program', 'year_level', 'phone',
            'can_manage_resources', 'is_active', 'date_joined', 'last_login', 'password',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_active']

    def validate_email(self, value):
        return _unique_email(value, self.instance)

    def validate_student_id(self, value):
        return _unique_student_id(value, self.instance)

    def validate(self, attrs):
        instance = self.instance
        role = attrs.get('role', instance.role if instance else User.Role.STUDENT)
        student_id = attrs.get('student_id', instance.student_id if instance else None)

        if instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'A password is required.'})
        if instance is not None:
            attrs.pop('password', None)  # passwords change through set-password only
            request = self.context.get('request')
            if request and instance.pk == request.user.pk and role != instance.role:
                raise serializers.ValidationError({'role': 'You cannot change your own role.'})

        if role == User.Role.STUDENT and not student_id:
            raise serializers.ValidationError({'student_id': 'Students need a student ID.'})
        if role != User.Role.STUDENT:
            attrs['student_id'] = None
            attrs['program'] = ''
            attrs['year_level'] = None
        if role != User.Role.LIBRARIAN:
            attrs['can_manage_resources'] = False

        if attrs.get('password'):
            candidate = User(
                email=attrs.get('email', ''),
                first_name=attrs.get('first_name', ''),
                last_name=attrs.get('last_name', ''),
            )
            try:
                _validate_password(attrs['password'], candidate)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({'password': exc.detail}) from exc
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(trim_whitespace=False)

    def validate_new_password(self, value):
        return _validate_password(value, self.context.get('target_user'))


class StudentSummarySerializer(serializers.ModelSerializer):
    """Compact student record for pickers and reservation details."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'student_id', 'email', 'program', 'year_level']
        read_only_fields = fields


class StudentLookupSerializer(serializers.ModelSerializer):
    """What one student may learn about another when inviting them: a name."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'student_id']
        read_only_fields = fields
