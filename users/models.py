from django.db import models
from django.contrib.auth.models import *
from django.core.validators import RegexValidator
from django.db.models.signals import post_save

from django.contrib.auth.models import Group

from departments.models import *
from students.models import StudentRecord
from django.conf import settings


class CustomGroup(models.Model):
    role = models.ForeignKey(
        Group,
        verbose_name="Role",
        related_name="group_role",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    roles = models.ManyToManyField(
        Group, verbose_name="Role", related_name="custom_group", blank=True
    )

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"


def meta_default():
    return {
        "batch": {},
        "prev_role": None,
        "formated_id": None,
        "student_records": {},
    }


class MyAccountManager(BaseUserManager):
    def get_queryset(self):
        if str(self.model.role) == "Student":
            return (
                super()
                .get_queryset()
                .select_related("institute", "department", "batch")
            )

        return super().get_queryset().select_related("institute", "department", "role")

    def create_user(self, email, username, password=None):
        print("create_user is called!")
        if not email:
            raise ValueError("Users must have an email address.")
        if not username:
            raise ValueError("Users must have a username.")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser):
    institute = models.ForeignKey(
        "institutes.Institute", on_delete=models.SET_NULL, null=True, blank=False
    )
    department = models.ForeignKey(
        "departments.Department", on_delete=models.SET_NULL, null=True, blank=False
    )

    id_suffix_validator = RegexValidator(regex=r"^[0-9]+$", message="Numbers only")
    suffix = models.CharField(
        validators=[id_suffix_validator], max_length=3, null=True, blank=False
    )
    role = models.ForeignKey(
        Group,
        verbose_name="Role",
        related_name="user_role",
        blank=False,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    metadata = models.JSONField(default=meta_default, null=True, blank=True)

    batch = models.ForeignKey(
        "departments.Batch",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="students_batch",
    )
    degree = models.ForeignKey(
        "institutes.Degree",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="student_degree",
    )
    # objects = MyAccountManager()
    prev_role = None

    def clean(self, *args, **kwargs):
        super(CustomUser, self).clean(*args, **kwargs)
        if self.batch and not str(self.role) == "Student":
            self.role = Group.objects.get(name="Student")
            # self.groups.set([self.role])
            self.department = self.batch.department
            self.institute = self.department.institute
            self.degree = self.batch.degree
        

            
        print("DONE")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"
        
    def get_publish_record(self):
        print("get_publish_record")
        if self.metadata.get("student_records") and len(
            self.metadata.get("student_records")
        ):

            records = self.metadata.get("student_records")
            print("records")
            print(records.keys())
            for k, v in records.items():
                print(v.keys())
                print(v.get("publish"))
                if v.get("publish"):
                    return v.get("data")

        return False

    def get_student_names_by_dept(institute_id, sheet_name):
        print('get_student_names_by_dept')
        print(f'SHEET NAME {sheet_name}')
        print(institute_id)
        
        qset = CustomUser.objects.filter(institute__id=institute_id, batch__name=sheet_name, role__name="Student")
        name_list = list(qset.values_list("username", flat=True))
        # qset = list(qset)
        print(qset)
        print(f'name_list {name_list}')
        return name_list, qset

    def get_subjects_header(self):
        record = StudentRecord.objects.filter(student=self, publish=True).last()
        if record:
            source = record.data
            if source:
                subjects = source.get("Subjects")

                print(subjects)
                data = {
                    "total_credits_completed_in_this_term": "",
                    "total_credits_taken_in_this_term": "",
                    "failed_subject": "",
                    "result": "",
                    "term_gpa": "",
                    "cgpa": "",
                }
                for k, item in source.items():
                    print(f"source {k}")
                    print(f"val {item}")
                    if not k == "Subjects":
                        f = k.lower().replace("  ", "_").replace(" ", "_")
                        if f.startswith("total_credits_taken_in_this_term"):
                            data["total_credits_taken_in_this_term"] = item
                        if f.startswith("total_credits_completed_in_this_term"):
                            data["total_credits_completed_in_this_term"] = item
                        if f.startswith("failed_subject"):
                            data["failed_subject"] = item
                        if f.startswith("result"):
                            data["result"] = item
                        if f.startswith("cgpa"):
                            data["cgpa"] = item
                        if f.endswith("gi_of_the_term"):
                            data["term_gpa"] = item

                print(data)
                return data
        return False

    def get_grade_results(self):
        records = StudentRecord.objects.filter(student=self, publish=True).order_by('record__level', 'record__term')
        print(f"RECORDS \n{records}")
        return records

    def get_publish_results(self):
        records = StudentRecord.objects.filter(student=self, publish=True, retake=False).order_by('record__level', 'record__term')
        
        print(f"RECORDS \n{records}")
        return records
        
    def set_last_seen(self, d):
        self.metadata['last_seen'] = d
        self.save()

class OnlineUsers(models.Model):

	# all users who are authenticated and viewing the chat
	title 				= models.CharField(max_length=255, unique=True, blank=False,)
	users 				= models.JSONField(null=True, blank=True, default=dict())

	def __str__(self):
		return self.title

	def connect_user(user):
		"""
		return true if user is added to the users list
		"""
		if not str(user.role) == 'Student':
			user_id = user.id

			self = OnlineUsers.objects.first()
			connected = False
			print("connect_USER!")
			print(user_id)
			print(self)
			print(self.users)
			print(self.users.get(str(user_id)))

			if not self.users.get(str(user_id)):
				connected = True
				user.set_last_seen('Online')
				
			self.users[str(user_id)] = {
										'connected': True,
									}
			self.save()
			
			print("___________________END")
			return connected 

	def disconnect_user(user_id):
		"""
		return true if user is removed from the users list
		"""
		self = OnlineUsers.objects.first()

		is_user_removed = False
		if self.users.get(str(user_id)):
			self.users[str(user_id)] = {
										'connected': False,
									}
			self.save()

			is_user_removed = True

		return is_user_removed
	
	def is_user_connected(user):
		self = OnlineUsers.objects.first()

		connected = False
		if self.users.get(str(user.id)):
			if self.users[str(user.id)]['connected']:
				connected = True
			else:
				self.users.pop(str(user.id), None)
				self.save()
				d = str(datetime.now())
				user.set_last_seen(d)

		connected_users = len(OnlineUsers.get())
		return connected, connected_users

	def get():
		self = OnlineUsers.objects.first()
		data = []
		if self:
			for k,v in self.users.items():
				data.append(int(k))
				
		return data


instance = OnlineUsers.objects.first()
if not instance:
    OnlineUsers.objects.create(title='All online users')

def post_save_receiver(sender, instance, created, **kwargs):
    pass


post_save.connect(post_save_receiver, sender=settings.AUTH_USER_MODEL)
