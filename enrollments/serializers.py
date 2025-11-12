from rest_framework import serializers

from course.serializers import ClassSerializer
from accounts.serializers import CustomUserSerializer

from .models import ClassEnrollment


class ClassEnrollmentSerializer(serializers.ModelSerializer):

    class_data = ClassSerializer(source='class_enrolled', read_only=True)
    student_data = CustomUserSerializer(source='student', read_only=True)
    
    # Flat fields for easier frontend access
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_email = serializers.EmailField(source='student.email', read_only=True)
    student_id = serializers.IntegerField(source='student.id', read_only=True)
    student_is_active = serializers.BooleanField(source='student.is_active', read_only=True)
    course_title = serializers.CharField(source='class_enrolled.title', read_only=True)
    course_id = serializers.IntegerField(source='class_enrolled.id', read_only=True)

    class Meta:
        model = ClassEnrollment
        fields = "__all__"

    def validate(self, validated_data):
        # Validate price doesn't exceed class price
        class_enrolled = validated_data.get('class_enrolled')
        price = validated_data.get('price')
        
        if class_enrolled and price is not None:
            class_price = class_enrolled.price
            
            # If class is free, price must be 0 or None
            if (not class_price or class_price == 0):
                if price > 0:
                    raise serializers.ValidationError({
                        'price': f'This class is free. Amount paid cannot exceed $0.00.'
                    })
            else:
                # Price cannot exceed class price
                if price > class_price:
                    raise serializers.ValidationError({
                        'price': f'Amount paid cannot exceed the class price of ${class_price}. You entered ${price}.'
                    })
        
        # Create temporary instance for validation
        instance = ClassEnrollment(**validated_data)
        instance.clean()
        return validated_data


# Legacy alias for backward compatibility
CourseEnrollmentSerializer = ClassEnrollmentSerializer

