from django import template
# আপনার অ্যাপের নাম 'your_app_name' এর জায়গায় বসিয়ে দিন (যেমন: from core.models import ...)
from main_app.models import Professor, ProfessorUpdateRequest, ProfileClaimRequest

register = template.Library()

@register.simple_tag
def get_pending_profiles_count():
    # যেসব প্রফেসর প্রোফাইল এখনো ভেরিফাই হয়নি
    return Professor.objects.filter(is_verified=False).count()

@register.simple_tag
def get_pending_updates_count():
    # যেসব প্রোফাইল আপডেট রিকোয়েস্ট এখনো অ্যাপ্রুভ হয়নি
    return ProfessorUpdateRequest.objects.filter(is_approved=False).count()

@register.simple_tag
def get_pending_claims_count():
    # যেসব প্রোফাইল ক্লেইম রিকোয়েস্ট এখনো অ্যাপ্রুভ হয়নি
    return ProfileClaimRequest.objects.filter(is_approved=False).count()