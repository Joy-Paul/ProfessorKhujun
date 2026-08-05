from django.contrib import admin
from django.contrib import messages
from .models import Professor, University, Review, StudentProfile, ProfessorUpdateRequest, ProfileClaimRequest, SubjectDeadline, Article

# সাবজেক্ট ডেডলাইনকে ইউনিভার্সিটির ভেতরে দেখানোর জন্য Inline ক্লাস
class SubjectDeadlineInline(admin.TabularInline):
    model = SubjectDeadline
    extra = 1  # ডিফল্টভাবে ১টি ফাঁকা সারি দেখাবে

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'fall_intl_deadline', 'spring_intl_deadline')
    search_fields = ('name', 'country')
    inlines = [SubjectDeadlineInline]

@admin.register(SubjectDeadline)
class SubjectDeadlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'university', 'degree_level', 'program_type', 'is_certificate')
    search_fields = ('name', 'university__name')
    list_filter = ('university', 'degree_level', 'program_type', 'is_certificate')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('university', 'name', 'degree_level', 'program_type', 'is_certificate')
        }),
        ('Priority Deadline', {
            'fields': ('priority_deadline',)
        }),
        ('Fall Deadlines', {
            'fields': ('fall_intl_deadline', 'fall_dom_deadline')
        }),
        ('Spring Deadlines', {
            'fields': ('spring_intl_deadline', 'spring_dom_deadline')
        }),
        ('Summer Deadlines', {
            'fields': ('summer_intl_deadline', 'summer_dom_deadline')
        }),
    )

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
    list_editable = ('is_verified',)

# ==========================================
# ৫. Professor Update Request Admin
# ==========================================
@admin.register(ProfessorUpdateRequest)
class UpdateRequestAdmin(admin.ModelAdmin):
    list_display = ('professor', 'short_request', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('professor__name', 'requested_changes')
    
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
            prof = claim.professor
            # প্রফেসরের সাথে ইউজার লিঙ্ক করা হচ্ছে
            prof.user = claim.user
            # প্রোফাইলটি ভেরিফাইড করে দেওয়া হচ্ছে
            prof.is_verified = True
            prof.save()
            
            # ক্লেইমটি অ্যাপ্রুভ করা হলো
            claim.is_approved = True
            claim.save()
            
            # একই প্রফেসরের জন্য অন্য কোনো ইউজারের পেন্ডিং রিকোয়েস্ট থাকলে তা ডিলিট করে দেওয়া হচ্ছে
            ProfileClaimRequest.objects.filter(professor=prof, is_approved=False).delete()
            
        self.message_user(request, "নির্বাচিত ক্লেইমগুলো অ্যাপ্রুভ করা হয়েছে এবং প্রোফাইলগুলো ভেরিফাইড হয়েছে।")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'read_time', 'views', 'created_at')
    search_fields = ('title', 'category')
    list_filter = ('category', 'created_at')