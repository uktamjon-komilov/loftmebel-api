from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not password:
            raise ValueError("You must provide password.")
        
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)

        return user
    

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)

        return user