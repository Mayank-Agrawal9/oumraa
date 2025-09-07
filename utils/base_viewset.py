import re

from rest_framework import response, status, viewsets, permissions


class BaseViewSetSetup(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_classes = {}
    default_serializer_class = None
    lookup_field = 'id'

    # this will enable single line response, you just have to set up with your action name and True/False
    enable_single_line_response = {
        'create': False,
        'update': False
    }
    # this setup is for handle the single line response message, you must have to define your function in your
    # model as @property and register with your action in 'single_line_response_functions'
    register_response_functions = {
        'create': 'object_created_message',
        'update': 'object_updated_message'
    }
    '''
    this is to check the unique constraint. sometimes we just want to create maximum one entry based on a specific 
    field(i.e. any unique field)
    "validate_unique" is to determine your decision that, do you want this feature or not. default it is False
    if you set it to True then you have to set the field name(on which it will check already exist or not)
    if you cannot access the field directly then you can setup the lookup. 
    Ex: unique_field_name="user" and you try to check based on username then you have to set the lookup = "lookup"
    and it will check like 
    >>> YourModel.objects.filter(user__username="your_username")
    "if_found_then_return" is to determine that if any object found then you return an error as the response or return
    the previous object
    If you want to return your previous stored object then you have to set the serializer, which will serialize the 
    previous_object
    * It will only work for create action
    '''
    unique_constraint_setup = {
        'enable': False,
        'unique_field_name': None,
        'lookup': 'id',
        'if_found_then_return': 'error',     # 'error/previous_response'
        'serializer': None
    }

    @property
    def unique_constraint_field(self):
        return self.unique_constraint_setup.get('unique_field_name')

    @property
    def default_unique_constraint_error_message(self):
        return 'One entry already exists for this %s' % self.unique_constraint_field

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def get_response_data(self):
        return {'detail': getattr(self.queryset.model(), self.register_response_functions.get(self.action))}

    def return_response(self, response_payload=None, extra_data=None, extra_data_key=None):
        # this function can be useful where, "CustomCreateMixin" is not inherited
        res = {}
        if self.enable_single_line_response.get(self.action):
            res = self.get_response_data()
        elif response_payload:
            res = response_payload

        # you can pass some extra_data along with the response
        # to do that, you just have to pass the 'extra_data_key' and 'extra_data'
        # ex: extra_data_key = 'token', extra_data = 'FSISKDJSOTDSAWXJHAXH'
        # so it will add with your response
        if extra_data and extra_data_key:
            res.update({extra_data_key: extra_data})

        return response.Response(res, status=status.HTTP_201_CREATED)

    def list_action_paginated_response(self, queryset, serializer_context=None, serializer_class=None):
        paginate = self.request.GET.get('paginate', '0')
        if not re.match("^[0-1]$", paginate):
            return response.Response({'detail': 'Invalid paginate value.'}, status=status.HTTP_400_BAD_REQUEST)
        ctx = serializer_context if serializer_context else {}
        if paginate == '1':
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = serializer_class(page, many=True, context=ctx) if serializer_class else\
                    self.get_serializer(page, many=True, context=ctx)
                return self.get_paginated_response(serializer.data)
        serializer = serializer_class(queryset, many=True, context=ctx) if serializer_class else \
            self.get_serializer(queryset, many=True, context=ctx)
        return response.Response(serializer.data)