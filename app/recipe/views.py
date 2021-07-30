from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient, Recipe
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


class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""
    serializer_class = serializers.RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def _params_to_ints(self, qs):
        """Convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve the recipes for the authenticated user"""
        # Fetch the tags and ingredients params from the query
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')

        # basic queryset
        queryset = self.queryset

        # filter the query further based on the tags or ingredients
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        # Finally return the query filtered on user now
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on list or retrieve"""
        if self.action == 'retrieve':
            # If the action is retrieve (means detail of a recipe is retrieved)
            # return the detail serializer otherwise just return the default
            return serializers.RecipeDetailSerializer
        # self.action is upload_image and not upload-image because the action
        # is same as the function name defined
        elif self.action == 'upload_image':
            # If the action is to upload the image, then return image-upload
            # serializer
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new Recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        # As we have set the detail=True in the decorator, that means that we
        # will be accessing a single specific recipe item in the DB and not the
        # full collection of recipes so the URL will be:
        # /recipe/recipes/<ID>/upload-image and not the standard:
        # /recipe/recipes/upload-image
        # The function self.get_object() hence retrieves the object which is
        # being addressed
        recipe = self.get_object()

        # The get serializer helper function returns the serializer defined
        # for this view. The recipe object is passed so that when we call the
        # serializer's save method, that particular object is saved
        # the second argument 'data' is used to validate the data passed in the
        # request. Explanation: https://www.udemy.com/course/django-python-
        # advanced/learn/lecture/12712743#questions/9787036
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
