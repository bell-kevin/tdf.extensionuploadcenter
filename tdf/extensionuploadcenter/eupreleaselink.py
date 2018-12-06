from tdf.extensionuploadcenter import MessageFactory as _
from plone.app.textfield import RichText
from plone.supermodel import model
from zope import schema
from plone.autoform import directives as form
from plone.dexterity.browser.view import DefaultView
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import directlyProvides
from plone.indexer.decorator import indexer

from zope.security import checkPermission
from zope.interface import invariant, Invalid
from Acquisition import aq_inner, aq_parent, aq_get, aq_chain
from plone.namedfile.field import NamedBlobFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget

from plone.directives import form
from zope import schema

from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory
from Products.validation import V_REQUIRED
from plone import api
from z3c.form import validator
from plone.uuid.interfaces import IUUID
import re

checkfileextension = re.compile(
    r"^.*\.(oxt|OXT)").match


def validatelinkedfileextension(value):
    if not checkfileextension(value):
        raise Invalid(u'You could only link to an URL (a file) that is a LibreOffice '
                      u'extension file with a proper file extension.')
    return True


def vocabAvailLicenses(context):
    """ pick up licenses list from parent """

    license_list = getattr(context.__parent__, 'available_licenses', [])
    terms = []
    for value in license_list:
        terms.append(SimpleTerm(value, token=value.encode('unicode_escape'), title=value))
    return SimpleVocabulary(terms)


directlyProvides(vocabAvailLicenses, IContextSourceBinder)


def vocabAvailVersions(context):
    """ pick up the program versions list from parent """

    versions_list = getattr(context.__parent__, 'available_versions', [])
    terms = []
    for value in versions_list:
        terms.append(SimpleTerm(value, token=value.encode('unicode_escape'), title=value))
    return SimpleVocabulary(terms)


directlyProvides(vocabAvailVersions, IContextSourceBinder)


def vocabAvailPlatforms(context):
    """ pick up the list of platforms from parent """

    platforms_list = getattr(context.__parent__, 'available_platforms', [])
    terms = []
    for value in platforms_list:
        terms.append(SimpleTerm(value, token=value.encode('unicode_escape'), title=value))
    return SimpleVocabulary(terms)


directlyProvides(vocabAvailPlatforms, IContextSourceBinder)

yesnochoice = SimpleVocabulary(
    [SimpleTerm(value=0, title=_(u'No')),
     SimpleTerm(value=1, title=_(u'Yes')), ]
)


@provider(IContextAwareDefaultFactory)
def getContainerTitle(self):
    return (self.aq_inner.title)


@provider(IContextAwareDefaultFactory)
def contactinfoDefault(context):
    return context.contactAddress


@provider(IContextAwareDefaultFactory)
def legal_declaration_title(context):
    context = context.aq_inner.aq_parent
    return context.title_legaldisclaimer


@provider(IContextAwareDefaultFactory)
def legal_declaration_text(context):
    context = context.aq_inner.aq_parent
    return context.legal_disclaimer


class AcceptLegalDeclaration(Invalid):
    __doc__ = _(u"It is necessary that you accept the Legal Declaration")


class IEUpReleaseLink(model.Schema):
    form.mode(projecttitle='hidden')
    projecttitle = schema.TextLine(
        title=_(u"The Computed Project Title"),
        description=_(u"The release title will be computed from the parent project title."),
        defaultFactory=getContainerTitle
    )

    releasenumber = schema.TextLine(
        title=_(u"Release Number"),
        description=_(u"Release Number (up to twelf chars)"),
        default=_(u"1.0"),
        max_length=12
    )

    description = schema.Text(
        title=_(u"Release Summary"),
    )

    form.primary('details')
    details = RichText(
        title=_(u"Full Release Description"),
        required=False
    )

    form.primary('changelog')
    changelog = RichText(
        title=_(u"Changelog"),
        description=_(u"A detailed log of what has changed since the previous release."),
        required=False,
    )

    form.widget(licenses_choice=CheckBoxFieldWidget)
    licenses_choice = schema.List(
        title=_(u'License of the uploaded file'),
        description=_(u"Please mark one or more licenses you publish your release."),
        value_type=schema.Choice(source=vocabAvailLicenses),
        required=True,
    )

    form.widget(compatibility_choice=CheckBoxFieldWidget)
    compatibility_choice = schema.List(
        title=_(u"Compatible with versions of LibreOffice"),
        description=_(u"Please mark one or more program versions with which this release is compatible with."),
        value_type=schema.Choice(source=vocabAvailVersions),
        required=True,
    )

    form.mode(title_declaration_legal='display')
    title_declaration_legal = schema.TextLine(
        title=_(u""),
        required=False,
        defaultFactory=legal_declaration_title
    )

    form.mode(declaration_legal='display')
    declaration_legal = schema.Text(
        title=_(u""),
        required=False,
        defaultFactory=legal_declaration_text
    )

    accept_legal_declaration = schema.Bool(
        title=_(u"Accept the above legal disclaimer"),
        description=_(u"Please declare that you accept the above legal disclaimer."),
        required=True
    )

    contact_address2 = schema.TextLine(
        title=_(u"Contact email-address"),
        description=_(u"Contact email-address for the project."),
        required=False,
        defaultFactory=contactinfoDefault
    )

    source_code_inside = schema.Choice(
        title=_(u"Is the source code inside the extension?"),
        vocabulary=yesnochoice,
        required=True
    )

    link_to_source = schema.URI(
        title=_(u"Please fill in the Link (URL) to the Source Code."),
        required=False
    )

    link_to_file = schema.URI(
        title=_(u"The Link to the file of the release"),
        description=_(u"Please insert a link to your extension file."),
        required=True,
        constraint=validatelinkedfileextension
    )

    external_file_size = schema.Float(
        title=_(u"The size of the external hosted file"),
        description=_(
            u"Please fill in the size in kilobyte of the external hosted file (e.g. 633, if the size is 633 kb)"),
        required=False
    )

    form.widget(platform_choice=CheckBoxFieldWidget)
    platform_choice = schema.List(
        title=_(u"First linked file is compatible with the Platform(s)"),
        description=_(u"Please mark one or more platforms with which the uploaded file is compatible."),
        value_type=schema.Choice(source=vocabAvailPlatforms),
        required=True,
    )

    form.mode(information_further_file_uploads='display')
    form.primary('information_further_file_uploads')
    information_further_file_uploads = RichText(
        title=_(u"Further linked files for this Release"),
        description=_(
            u"If you want to link more files for this release, e.g. because "
            u"there are files for other operating systems, you'll find the "
            u"fields to link this files on the next registers, e.g. 'Second linked file' "
            u"for this Release'."),
        required=False
    )

    model.fieldset('fieldset1',
                   label=_(u"Second linked file"),
                   fields=['link_to_file1',
                           'external_file_size1',
                           'platform_choice1']
                   )

    model.fieldset('fieldset2',
                   label=_(u"Third linked file"),
                   fields=['link_to_file2',
                           'external_file_size2',
                           'platform_choice2']
                   )

    model.fieldset('fieldset3',
                   label=_(u"Fourth linked file"),
                   fields=['link_to_file3',
                           'external_file_size3',
                           'platform_choice3']
                   )

    model.fieldset('fieldset4',
                   label=_(u"Fifth linked file"),
                   fields=['link_to_file4',
                           'external_file_size4',
                           'platform_choice4']
                   )

    model.fieldset('fieldset5',
                   label=_(u"Sixth linked file"),
                   fields=['link_to_file5',
                           'external_file_size5',
                           'platform_choice5']
                   )

    link_to_file1 = schema.URI(
        title=_(u"The Link to the file of the release"),
        description=_(u"Please insert a link to your extension file."),
        required=False,
        constraint=validatelinkedfileextension
    )

    external_file_size1 = schema.Float(
        title=_(u"The size of the external hosted file"),
        description=_(u"Please fill in the size in kilobyte of the external "
                      u"hosted file (e.g. 633, if the size is 633 kb)"),
        required=False
    )

    form.widget(platform_choice1=CheckBoxFieldWidget)
    platform_choice1 = schema.List(
        title=_(u"Second linked file is compatible with the Platform(s)"),
        description=_(u"Please mark one or more platforms with which the linked file is compatible."),
        value_type=schema.Choice(source=vocabAvailPlatforms),
        required=True,
    )

    link_to_file2 = schema.URI(
        title=_(u"The Link to the file of the release"),
        description=_(u"Please insert a link to your extension file."),
        required=False,
        constraint=validatelinkedfileextension
    )

    external_file_size2 = schema.Float(
        title=_(u"The size of the external hosted file"),
        description=_(u"Please fill in the size in kilobyte of the external "
                      u"hosted file (e.g. 633, if the size is 633 kb)"),
        required=False
    )

    form.widget(platform_choice2=CheckBoxFieldWidget)
    platform_choice2 = schema.List(
        title=_(u"Third linked file is compatible with the Platform(s)"),
        description=_(u"Please mark one or more platforms with which the linked file is compatible."),
        value_type=schema.Choice(source=vocabAvailPlatforms),
        required=True
    )

    link_to_file3 = schema.URI(
        title=_(u"The Link to the file of the release"),
        description=_(u"Please insert a link to your extension file."),
        required=False,
        constraint=validatelinkedfileextension
    )

    external_file_size3 = schema.Float(
        title=_(u"The size of the external hosted file"),
        description=_(u"Please fill in the size in kilobyte of the external "
                      u"hosted file (e.g. 633, if the size is 633 kb)"),
        required=False
    )

    form.widget(platform_choice3=CheckBoxFieldWidget)
    platform_choice3 = schema.List(
        title=_(u"Fourth linked file is compatible with the Platform(s)"),
        description=_(u"Please mark one or more platforms with which the linked file is compatible."),
        value_type=schema.Choice(source=vocabAvailPlatforms),
        required=True,
    )

    link_to_file4 = schema.URI(
        title=_(u"The Link to the file of the release"),
        description=_(u"Please insert a link to your extension file."),
        required=False,
        constraint=validatelinkedfileextension
    )

    external_file_size4 = schema.Float(
        title=_(u"The size of the external hosted file"),
        description=_(u"Please fill in the size in kilobyte of the external "
                      u"hosted file (e.g. 633, if the size is 633 kb)"),
        required=False
    )

    form.widget(platform_choice4=CheckBoxFieldWidget)
    platform_choice4 = schema.List(
        title=_(u"Fifth linked file is compatible with the Platform(s)"),
        description=_(u"Please mark one or more platforms with which the linked file is compatible."),
        value_type=schema.Choice(source=vocabAvailPlatforms),
        required=True,
    )

    link_to_file5 = schema.URI(
        title=_(u"The Link to the file of the release"),
        description=_(u"Please insert a link to your extension file."),
        required=False,
        constraint=validatelinkedfileextension
    )

    external_file_size5 = schema.Float(
        title=_(u"The size of the external hosted file"),
        description=_(u"Please fill in the size in kilobyte of the external "
                      u"hosted file (e.g. 633, if the size is 633 kb)"),
        required=False
    )

    form.widget(platform_choice5=CheckBoxFieldWidget)
    platform_choice5 = schema.List(
        title=_(u"Sixth linked file is compatible with the Platform(s)"),
        description=_(u"Please mark one or more platforms with which the linked file is compatible."),
        value_type=schema.Choice(source=vocabAvailPlatforms),
        required=True,
    )

    @invariant
    def licensenotchoosen(value):
        if not value.licenses_choice:
            raise Invalid(_(u"Please choose a license for your release."))

    @invariant
    def compatibilitynotchoosen(data):
        if not data.compatibility_choice:
            raise Invalid(_(u"Please choose one or more compatible product versions for your release."))

    @invariant
    def legaldeclarationaccepted(data):
        if data.accept_legal_declaration is not True:
            raise AcceptLegalDeclaration(_(u"Please accept the Legal Declaration about "
                                           U"your Release and your linked File"))

    @invariant
    def testingvalue(data):
        if data.source_code_inside is not 1 and data.link_to_source is None:
            raise Invalid(_(u"You answered the question, whether the source code is inside your extension with no "
                            u"(default answer). If this is the correct answer, please fill in the Link (URL) "
                            u"to the Source Code."))

    @invariant
    def noOSChosen(data):
        if data.link_to_file is not None and data.platform_choice == []:
            raise Invalid(_(u"Please choose a compatible platform for the linked file."))


@indexer(IEUpReleaseLink)
def release_number(context, **kw):
    return context.releasenumber


def notifyExtensionHubReleaseLinkAdd(self, event):
    portal = api.portal.get()
    state = api.content.get_state(self)
    releasemessagereceipient = self.releaseAllert
    catalog = api.portal.get_tool(name='portal_catalog')
    results = catalog(Title=self.title)
    for brain in results:
        url = brain.getURL()

        category = list(self.category_choice)
        compatibility = list(self.compatibility_choice)
        licenses = list(self.licenses_choice)
        pf_list = \
            list(self.platform_choice) + list(self.platform_choice1) + \
            list(self.platform_choice2) + list(self.platform_choice3) + \
            list(self.platform_choice4) + list(self.platform_choice5)
        pf_set = set(pf_list)
        platform = list(pf_set)
        platform.sort()

    if state == 'final' and releasemessagereceipient is not None:
        api.portal.send_email(
            recipient=releasemessagereceipient,
            subject="New Release added",
            body=("""A new linked release was added and published with\ntitle: {}\nURL: {}\nCompatibility:{}\n
                  Categories: {}\nLicenses: {}\nPlatforms: {}""").format(self.title, url, compatibility,
                                                                         category, licenses, platform),
        )

    else:
        return None


class ValidateEUpReleaseLinkUniqueness(validator.SimpleFieldValidator):
    # Validate site-wide uniqueness of release titles.

    def validate(self, value):
        # Perform the standard validation first
        super(ValidateEUpReleaseLinkUniqueness, self).validate(value)

        if value is not None:
            if IEUpReleaseLink.providedBy(self.context):
                # The release number is the same as the previous value stored
                # in the object
                if self.context.releasenumber == value:
                    return None

            catalog = api.portal.get_tool(name='portal_catalog')
            # Differentiate between possible contexts (on creation or editing)
            # on creation the context is the container
            # on editing the context is already the object
            if IEUpReleaseLink.providedBy(self.context):
                query = '/'.join(self.context.aq_parent.getPhysicalPath())
            else:
                query = '/'.join(self.context.getPhysicalPath())

            result = catalog({
                'path': {'query': query, 'depth': 1},
                'portal_type': ['tdf.extensionuploadcenter.euprelease',
                                'tdf.extensionuploadcenter.eupreleaselink'],
                'release_number': value})

            if len(result) > 0:
                raise Invalid(_(u"The release number is already in use. Please choose another one."))


validator.WidgetValidatorDiscriminators(
    ValidateEUpReleaseLinkUniqueness,
    field=IEUpReleaseLink['releasenumber'],
)


class EUpReleaseLinkView(DefaultView):
    def canPublishContent(self):
        return checkPermission('cmf.ModifyPortalContent', self.context)

    def releaseLicense(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        path = "/".join(self.context.getPhysicalPath())
        idx_data = catalog.getIndexDataForUID(path)
        licenses = idx_data.get('releaseLicense')
        return(r for r in licenses)

    def linkedreleaseCompatibility(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        path = "/".join(self.context.getPhysicalPath())
        idx_data = catalog.getIndexDataForUID(path)
        compatibility = idx_data.get('getCompatibility')
        return(r for r in compatibility)
