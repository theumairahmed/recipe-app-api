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
class BaseRecipeAttrViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin):
    """Base viewset for user owned recipe attributes"""
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    # We override this function present in GenericViewSet(GenericAPIView) class
    # which is then used by ListModelMixin to get the queryset that it should
    # list in response.
    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    # We override this function present in CreateModelMixin to define the
    # functionality that we should perform while creating the model
    def perform_create(self, serializer):
        """Create a new object"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database"""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database"""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
