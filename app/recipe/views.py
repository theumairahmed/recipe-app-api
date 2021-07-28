from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient
from recipe import serializers


# viewsets.GenericViewSet extended to implement changes in get_queryset
# functionality that is to be used for ListModelMixin

# mixins.ListModelMixin extended to get the boilerplate code for 'list' viewset
# operation

# mixins.CreateModelMixin extended to get the boilerplate code for 'create'
# viewset operation
class TagViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.CreateModelMixin):
    """Manage tags in the database"""
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer

    # We override this function present in GenericViewSet(GenericAPIView) class
    # which is then used by ListModelMixin to get the queryset that it should
    # list in response.
    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    # We override this function present in CreateModelMixin to define the
    # functionality that we should perform while creating the model
    def perform_create(self, serializer):
        """Create a new tag"""
        serializer.save(user=self.request.user)


class IngredientViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Manage ingerdients in the database"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by('-name')
