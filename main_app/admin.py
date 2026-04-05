from django.contrib import admin
from django.contrib import messages
from .models import Professor, University, Review, StudentProfile, ProfessorUpdateRequest
from .models import ProfileClaimRequest

# ==========================================
# ১. University Admin
# ==========================================
admin.site.register(University)

# ==========================================
# ২. Professor Admin (With Verification Action)
# ==========================================
@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('name', 'university', 'is_verified')
    list_filter = ('is_verified', 'university')
    actions = ['approve_professors']

    @admin.action(description="Selected প্রফেসরদের ভেরিফাই করুন (Live on Site)")
    def approve_professors(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, "প্রোফাইলগুলো সফলভাবে ভেরিফাই করা হয়েছে।")

# ==========================================
# ৩. Review Admin
# ==========================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('professor', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'professor')

# ==========================================
# ৪. Student Profile Admin (For Verification)
# ==========================================
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified')
    list_filter = ('is_verified',)
    list_editable = ('is_verified',) # অ্যাডমিন এখান থেকেই টিক দিয়ে ভেরিফাই করতে পারবে

# ==========================================
# ৫. Professor Update Request Admin
# ==========================================
@admin.register(ProfessorUpdateRequest)
class UpdateRequestAdmin(admin.ModelAdmin):
    list_display = ('professor', 'short_request', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('professor__name', 'requested_changes')
    
    # রিকোয়েস্টগুলো শুধু পড়া যাবে
    readonly_fields = ('professor', 'requested_changes', 'created_at')
    actions = ['mark_as_approved']

    def short_request(self, obj):
        return obj.requested_changes[:50] + '...' if len(obj.requested_changes) > 50 else obj.requested_changes
    short_request.short_description = 'Requested Changes'

    @admin.action(description="Mark selected requests as Approved")
    def mark_as_approved(self, request, queryset):
        updated_count = queryset.update(is_approved=True)
        self.message_user(request, f"{updated_count} update request(s) marked as approved.", messages.SUCCESS)

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['is_approved'].help_text = "অ্যাপ্রুভ করার আগে প্রফেসরের মেইন প্রোফাইলে গিয়ে পরিবর্তনগুলো নিজ হাতে আপডেট করে আসুন।"
        return super().render_change_form(request, context, *args, **kwargs)
    

@admin.register(ProfileClaimRequest)
class ProfileClaimAdmin(admin.ModelAdmin):
    list_display = ('user', 'professor', 'created_at', 'is_approved')
    actions = ['approve_claims']

    @admin.action(description="Selected ক্লেইমগুলো অ্যাপ্রুভ করুন")
    def approve_claims(self, request, queryset):
        for claim in queryset:
            # প্রফেসরের ইউজার ফিল্ডে রিকোয়েস্ট করা ইউজারকে সেট করে দেওয়া
            prof = claim.professor
            prof.user = claim.user
            prof.save()
        
        queryset.update(is_approved=True)
        self.message_user(request, "প্রোফাইল ক্লেইম সফলভাবে অ্যাপ্রুভ করা হয়েছে।")